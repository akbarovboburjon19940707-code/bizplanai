import asyncio
import os

import pytest

from tests.conftest import PLAN_INPUT, auth, register

pytestmark = pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL", "").startswith("postgres"),
                                reason="haqiqiy parallel tranzaksiyalar faqat Postgres'da tekshiriladi")


async def test_quota_holds_under_parallel_requests(client, monkeypatch):
    import app.modules.plans.service as svc

    async def no_generation(plan_id):  # faqat kvota mantiqini tekshiramiz
        return None
    monkeypatch.setattr(svc, "run_generation", no_generation)
    token = await register(client)
    results = await asyncio.gather(*[client.post("/v1/plans", json={"input": PLAN_INPUT}, headers=auth(token))
                                     for _ in range(10)])
    codes = sorted(r.status_code for r in results)
    assert codes.count(202) == 3 and codes.count(429) == 7, codes


async def test_double_payme_perform_grants_once(client):
    import base64
    import time
    from sqlalchemy import select
    from app.db.session import sessionmaker
    from app.models import Entitlement

    h = {"Authorization": "Basic " + base64.b64encode(b"Paycom:payme-key").decode()}
    token = await register(client)
    prod = (await client.get("/v1/catalog/products", params={"limit": 1})).json()["items"][0]
    pid = (await client.post("/v1/payments", json={"kind": "catalog", "target_id": prod["id"], "provider": "payme"},
                             headers=auth(token))).json()["payment"]["id"]
    await client.post("/v1/payments/payme", headers=h, json={"id": 1, "method": "CreateTransaction", "params": {
        "id": "pmx", "time": int(time.time() * 1000), "amount": prod["price_som"] * 100, "account": {"order_id": pid}}})
    await asyncio.gather(*[client.post("/v1/payments/payme", headers=h,
                                       json={"id": i, "method": "PerformTransaction", "params": {"id": "pmx"}})
                           for i in range(5)])
    async with sessionmaker()() as s:
        assert len((await s.scalars(select(Entitlement))).all()) == 1
