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
    # eski tokenni qayta ishlatish grace oynasidan keyin aniqlanadi:
    # test_refresh_reuse_after_grace_still_detected


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


async def test_concurrent_refresh_grace_does_not_kill_sessions(client):
    """Ikki tab bir vaqtda eski cookie bilan refresh qilsa, hamma sessiya yopilmasligi kerak."""
    await register(client)
    cookie = client.cookies.get("bp_refresh")
    client.cookies.clear()
    tab1 = await client.post("/v1/auth/refresh", cookies={"bp_refresh": cookie})
    tab2 = await client.post("/v1/auth/refresh", cookies={"bp_refresh": cookie})
    assert tab1.status_code == 200 and tab2.status_code == 200
    for r in (tab1, tab2):
        nxt = await client.post("/v1/auth/refresh", cookies={"bp_refresh": r.cookies.get("bp_refresh")})
        assert nxt.status_code == 200


async def test_refresh_reuse_after_grace_still_detected(client):
    from datetime import timedelta

    from sqlalchemy import select

    from app.db.session import sessionmaker
    from app.models import RefreshToken
    from app.modules.auth.service import REFRESH_GRACE_SECONDS

    await register(client)
    cookie = client.cookies.get("bp_refresh")
    client.cookies.clear()
    fresh = await client.post("/v1/auth/refresh", cookies={"bp_refresh": cookie})
    assert fresh.status_code == 200
    async with sessionmaker()() as s:
        for t in (await s.scalars(select(RefreshToken).where(RefreshToken.revoked_at.is_not(None)))).all():
            t.revoked_at -= timedelta(seconds=REFRESH_GRACE_SECONDS + 5)
        await s.commit()
    r = await client.post("/v1/auth/refresh", cookies={"bp_refresh": cookie})
    assert r.status_code == 401 and r.json()["error"]["code"] == "token_reused"
    r = await client.post("/v1/auth/refresh", cookies={"bp_refresh": fresh.cookies.get("bp_refresh")})
    assert r.status_code == 401  # hamma sessiya yopilgan


async def test_reuse_after_logout_is_not_graced(client):
    await register(client)
    cookie = client.cookies.get("bp_refresh")
    client.cookies.clear()
    assert (await client.post("/v1/auth/logout", cookies={"bp_refresh": cookie})).status_code == 204
    r = await client.post("/v1/auth/refresh", cookies={"bp_refresh": cookie})
    assert r.status_code == 401


async def test_login_lockout_counts_only_failures(client):
    from app.core.redis import get_redis
    from app.modules.auth.router import LOGIN_MAX_FAILS

    async def reset_ip_limit():  # IP bo'yicha umumiy limit (20/daq) bu testda raqam bo'yicha mantiqqa xalaqit bermasin
        for k in await get_redis().keys("rl:login:*"):
            await get_redis().delete(k)

    await register(client)
    good = {"phone": "+998901112233", "password": "parol12345"}
    bad = {**good, "password": "notogri123"}
    # muvaffaqiyatli kirishlar hisoblanmaydi (tez-tez kiradigan foydalanuvchi bloklanmaydi)
    for _ in range(LOGIN_MAX_FAILS + 2):
        assert (await client.post("/v1/auth/login", json=good)).status_code == 200
    # noto'g'ri urinishlar, to'g'ri kirish hisoblagichni tozalaydi
    await reset_ip_limit()
    for _ in range(LOGIN_MAX_FAILS - 1):
        assert (await client.post("/v1/auth/login", json=bad)).status_code == 401
    assert (await client.post("/v1/auth/login", json=good)).status_code == 200
    await reset_ip_limit()
    for _ in range(LOGIN_MAX_FAILS):
        assert (await client.post("/v1/auth/login", json=bad)).status_code == 401
    # endi to'g'ri parol bilan ham blok (IP dan qat'i nazar raqam bo'yicha)
    r = await client.post("/v1/auth/login", json=good)
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"
