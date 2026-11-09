import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

from tests.conftest import auth, register


async def test_register_login_me(client):
    token = await register(client, phone="90 111 22 33")
    r = await client.get("/v1/me", headers=auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["phone"] == "+998901112233"
    assert body["subscription"]["tariff_code"] == "basic"
    assert body["subscription"]["daily_limit"] == 3

    r = await client.post("/v1/auth/register", json={"phone": "+998901112233", "password": "boshqa12345"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "phone_taken"

    r = await client.post("/v1/auth/login", json={"phone": "+998901112233", "password": "notogri123"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "invalid_credentials"
    r = await client.post("/v1/auth/login", json={"phone": "+998901112233", "password": "parol12345"})
    assert r.status_code == 200 and r.json()["access_token"]


async def test_validation_error_format(client):
    r = await client.post("/v1/auth/register", json={"phone": "123", "password": "short"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


async def test_refresh_rotation_and_reuse_detection(client):
    await register(client)
    old_cookie = client.cookies.get("bp_refresh")
    r = await client.post("/v1/auth/refresh")
    assert r.status_code == 200
    assert client.cookies.get("bp_refresh") != old_cookie
    # eski tokenni qayta ishlatish -> barcha sessiyalar yopiladi
    r = await client.post("/v1/auth/refresh", json={"refresh_token": old_cookie}, cookies={"bp_refresh": ""})
    assert r.status_code == 401 and r.json()["error"]["code"] == "token_reused"


async def test_me_requires_auth(client):
    r = await client.get("/v1/me")
    assert r.status_code == 401
    r = await client.get("/v1/me", headers={"Authorization": "Bearer yaroqsiz"})
    assert r.status_code == 401


def _init_data(user: dict, bot_token="123456:TEST-TOKEN", auth_date=None) -> str:
    pairs = {"auth_date": str(auth_date or int(time.time())), "query_id": "AAH", "user": json.dumps(user)}
    check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    pairs["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(pairs)


async def test_telegram_webapp_login(client):
    good = _init_data({"id": 777, "first_name": "Ali", "username": "ali"})
    r = await client.post("/v1/auth/telegram/webapp", json={"init_data": good})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["telegram_username"] == "ali"
    # o'sha odam yana kirsa, yangi akkaunt yaratilmaydi
    r2 = await client.post("/v1/auth/telegram/webapp", json={"init_data": good})
    assert r2.json()["user"]["id"] == r.json()["user"]["id"]

    forged = _init_data({"id": 777}, bot_token="999:BOSHQA")
    assert (await client.post("/v1/auth/telegram/webapp", json={"init_data": forged})).status_code == 401
    old = _init_data({"id": 777}, auth_date=int(time.time()) - 200000)
    assert (await client.post("/v1/auth/telegram/webapp", json={"init_data": old})).status_code == 401


async def test_telegram_bot_login_flow(client):
    r = await client.post("/v1/auth/telegram/login-init")
    token = r.json()["token"]
    assert (await client.get("/v1/auth/telegram/login-poll", params={"token": token})).json()["status"] == "pending"

    update = {"message": {"text": f"/start login_{token}", "chat": {"id": 5}, "from": {"id": 555, "first_name": "Vali"}}}
    bad = await client.post("/v1/telegram/webhook", json=update, headers={"X-Telegram-Bot-Api-Secret-Token": "xato"})
    assert bad.status_code == 403
    ok = await client.post("/v1/telegram/webhook", json=update, headers={"X-Telegram-Bot-Api-Secret-Token": "hook-secret"})
    assert ok.status_code == 200

    r = await client.get("/v1/auth/telegram/login-poll", params={"token": token})
    assert r.json()["status"] == "authenticated" and r.json()["session"]["access_token"]
    # token bir martalik
    assert (await client.get("/v1/auth/telegram/login-poll", params={"token": token})).json()["status"] == "expired"


async def test_admin_requires_totp_and_role(client):
    from app.cli import create_admin
    from app.core.security import _totp_at

    token = await register(client)
    assert (await client.get("/v1/admin/stats", headers=auth(token))).status_code == 403

    await create_admin("+998909998877", "juda-kuchli-parol-123")
    r = await client.post("/v1/auth/login", json={"phone": "+998909998877", "password": "juda-kuchli-parol-123"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "totp_required"

    from sqlalchemy import select
    from app.db.session import sessionmaker
    from app.models import User
    async with sessionmaker()() as s:
        secret = (await s.scalar(select(User).where(User.phone == "+998909998877"))).totp_secret
    code = _totp_at(secret, int(time.time()) // 30)
    r = await client.post("/v1/auth/login", json={"phone": "+998909998877", "password": "juda-kuchli-parol-123",
                                                   "totp_code": code})
    assert r.status_code == 200
    stats = await client.get("/v1/admin/stats", headers=auth(r.json()["access_token"]))
    assert stats.status_code == 200 and stats.json()["users_total"] == 2
