from datetime import timedelta

from docx import Document
from sqlalchemy import update

from tests.conftest import PLAN_INPUT, auth, register


class FakeProvider:
    name = "fake"

    def __init__(self, fail=False):
        self.fail = fail

    async def complete(self, client, system, prompt):
        import httpx
        from app.ai.providers import Completion
        if self.fail:
            raise httpx.ConnectError("yo'q")
        return Completion(text=("Loyiha bozorda barqaror talabga ega. " * 40), tokens=500, provider=self.name)


async def test_ai_sections_appended_with_fallback(client, monkeypatch):
    import app.ai.service as ai
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "ai_enabled", True)
    monkeypatch.setattr(ai, "configured_providers", lambda s: [FakeProvider(fail=True), FakeProvider()])

    from app.db.session import sessionmaker
    from app.models import User
    token = await register(client)
    async with sessionmaker()() as s:
        await s.execute(update(User).values(plan_credits=1))
        await s.commit()
    plan = (await client.post("/v1/plans", json={"input": PLAN_INPUT}, headers=auth(token))).json()
    assert plan["status"] == "done" and plan["ai_used"] is True

    url = (await client.get(f"/v1/plans/{plan['id']}/download", headers=auth(token))).json()["url"]
    from app.core.security import decode_token
    from app.storage import get_storage
    path = get_storage().path_for(decode_token(url.rsplit("/", 1)[-1], "file")["key"])
    headings = [p.text for p in Document(path).paragraphs if p.style.name.startswith("Heading")]
    assert "Qo'shimcha tahlil" in headings and "SWOT tahlili" in headings


async def test_ai_budget_stops_calls(monkeypatch):
    import app.ai.service as ai
    from app.core.config import get_settings
    from app.core.redis import get_redis
    from app.core.security import utcnow
    monkeypatch.setattr(get_settings(), "ai_enabled", True)
    monkeypatch.setattr(ai, "configured_providers", lambda s: [FakeProvider()])
    await get_redis().set(f"ai:tokens:{utcnow():%Y-%m-%d}", get_settings().ai_daily_token_budget)
    assert await ai.generate_sections({}, {}) == {}


async def test_flush_views_and_stale_payments(client):
    from app.core.security import utcnow
    from app.db.session import sessionmaker
    from app.models import CatalogProduct, Payment
    from app.workers.settings import cancel_stale_payments, flush_views

    prod = (await client.get("/v1/catalog/products", params={"limit": 1})).json()["items"][0]
    for _ in range(3):
        assert (await client.post(f"/v1/catalog/products/{prod['id']}/view")).status_code == 204
    await flush_views({})
    async with sessionmaker()() as s:
        assert (await s.get(CatalogProduct, prod["id"])).views == prod["views"] + 3

    token = await register(client)
    pid = (await client.post("/v1/payments", json={"kind": "plan_credit", "provider": "click"},
                             headers=auth(token))).json()["payment"]["id"]
    async with sessionmaker()() as s:
        await s.execute(update(Payment).values(created_at=utcnow() - timedelta(hours=30)))
        await s.commit()
    await cancel_stale_payments({})
    async with sessionmaker()() as s:
        assert (await s.get(Payment, pid)).status == "cancelled"
