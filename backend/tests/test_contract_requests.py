"""frontend/docs/CONTRACT_REQUESTS.md dagi 1-4 so'rovlar."""
from tests.conftest import auth, register
from tests.test_admin import _admin_headers


async def test_email_can_be_cleared_and_none_keeps_it(client):
    token = await register(client)
    h = auth(token)
    assert (await client.patch("/v1/me", json={"email": "a@example.com"}, headers=h)).json()["email"] == "a@example.com"
    assert (await client.patch("/v1/me", json={"first_name": "Ali"}, headers=h)).json()["email"] == "a@example.com"
    assert (await client.patch("/v1/me", json={"email": None}, headers=h)).json()["email"] == "a@example.com"
    assert (await client.patch("/v1/me", json={"email": ""}, headers=h)).json()["email"] is None
    assert (await client.patch("/v1/me", json={"email": "yaroqsiz"}, headers=h)).status_code == 422


async def test_has_password_true_for_phone_and_false_for_telegram_users(client):
    me = (await client.post("/v1/auth/register", json={"phone": "+998901230000", "password": "parol12345"})).json()
    assert me["user"]["has_password"] is True

    token = (await client.post("/v1/auth/telegram/login-init")).json()["token"]
    update = {"message": {"text": f"/start login_{token}", "chat": {"id": 5}, "from": {"id": 4242, "first_name": "Tg"}}}
    from app.core.config import get_settings
    await client.post("/v1/telegram/webhook", json=update,
                      headers={"X-Telegram-Bot-Api-Secret-Token": get_settings().telegram_webhook_header_token})
    session = (await client.get("/v1/auth/telegram/login-poll", params={"token": token})).json()["session"]
    assert session["user"]["has_password"] is False
    me = (await client.get("/v1/me", headers=auth(session["access_token"]))).json()
    assert me["user"]["has_password"] is False


async def test_owned_lists_only_my_paid_catalog_products(client):
    token = await register(client)
    h = auth(token)
    assert (await client.get("/v1/catalog/owned")).status_code == 401
    assert (await client.get("/v1/catalog/owned", headers=h)).json() == {"product_ids": []}

    pid = (await client.get("/v1/catalog/products", params={"limit": 1})).json()["items"][0]["id"]
    pay = (await client.post("/v1/payments", json={"kind": "catalog", "target_id": pid, "provider": "manual"}, headers=h)).json()
    assert (await client.get("/v1/catalog/owned", headers=h)).json()["product_ids"] == []  # to'lanmaguncha yo'q
    approved = await client.post(f"/v1/admin/payments/{pay['payment']['id']}/approve", json={}, headers=await _admin_headers())
    assert approved.status_code == 200
    assert (await client.get("/v1/catalog/owned", headers=h)).json()["product_ids"] == [pid]

    other = await register(client, phone="+998901119999")
    assert (await client.get("/v1/catalog/owned", headers=auth(other))).json()["product_ids"] == []


async def test_pricing_exposes_plan_credit_price(client):
    assert (await client.get("/v1/pricing")).json() == {"plan_credit_price_som": 50000}
