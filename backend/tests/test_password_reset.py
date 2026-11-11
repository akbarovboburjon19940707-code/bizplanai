"""Parolni tiklash Telegram orqali: kontakt raqami hisobdagi raqamga mos kelsa yangi parol."""
from app.core.config import get_settings
from tests.conftest import auth, register

PHONE = "+998901112233"


def hook(client, message: dict):
    return client.post("/v1/telegram/webhook", json={"message": message},
                       headers={"X-Telegram-Bot-Api-Secret-Token": get_settings().telegram_webhook_header_token})


def contact_msg(phone: str, sender: int = 555, owner: int | None = 555, chat: int = 5):
    return {"chat": {"id": chat}, "from": {"id": sender, "first_name": "Vali"},
            "contact": {"phone_number": phone, "user_id": owner, "first_name": "Vali"}}


async def start_reset(client, phone=PHONE, chat=5, sender=555):
    r = await client.post("/v1/auth/password-reset/init", json={"phone": phone})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["bot_url"].endswith(f"?start=reset_{body['token']}") and body["expires_in"] == 600
    await hook(client, {"text": f"/start reset_{body['token']}", "chat": {"id": chat}, "from": {"id": sender, "first_name": "Vali"}})
    return body["token"]


async def poll(client, token):
    return (await client.get("/v1/auth/password-reset/poll", params={"token": token})).json()["status"]


async def test_reset_flow_logs_in_and_revokes_old_sessions(client):
    old_access = await register(client, PHONE, "eski-parol-123")
    old_refresh = client.cookies.get("bp_refresh")
    token = await start_reset(client)
    assert await poll(client, token) == "pending"
    # tasdiqlanmagan token bilan parol o'zgarmaydi
    early = await client.post("/v1/auth/password-reset/complete", json={"token": token, "new_password": "yangi-parol-123"})
    assert early.status_code == 400

    await hook(client, contact_msg("998901112233"))  # Telegram raqamni "+" siz yuboradi
    assert await poll(client, token) == "verified"

    short = await client.post("/v1/auth/password-reset/complete", json={"token": token, "new_password": "123"})
    assert short.status_code == 422
    done = await client.post("/v1/auth/password-reset/complete", json={"token": token, "new_password": "yangi-parol-123"})
    assert done.status_code == 200 and done.json()["session"]["access_token"]
    # bir martalik
    again = await client.post("/v1/auth/password-reset/complete", json={"token": token, "new_password": "boshqa-parol-1"})
    assert again.status_code == 400

    login = lambda pw: client.post("/v1/auth/login", json={"phone": PHONE, "password": pw})  # noqa: E731
    assert (await login("eski-parol-123")).status_code == 401
    assert (await login("yangi-parol-123")).status_code == 200
    # eski refresh token endi ishlamaydi
    client.cookies.clear()
    r = await client.post("/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 401
    assert (await client.get("/v1/me", headers=auth(old_access))).status_code == 200  # access 15 daqiqada o'zi tugaydi


async def test_wrong_or_foreign_contact_is_rejected(client):
    await register(client, PHONE, "eski-parol-123")
    token = await start_reset(client)
    await hook(client, contact_msg("+998901112233", owner=999))  # boshqa odamning kontakti
    assert await poll(client, token) == "pending"
    await hook(client, contact_msg("+998935554433"))  # boshqa raqam
    assert await poll(client, token) == "mismatch"
    r = await client.post("/v1/auth/password-reset/complete", json={"token": token, "new_password": "yangi-parol-123"})
    assert r.status_code == 400

    # bazada yo'q raqam: init baribir javob beradi (raqam borligi oshkor qilinmaydi), botda mos kelmaydi
    t2 = await start_reset(client, phone="+998977777777", chat=6, sender=666)
    await hook(client, contact_msg("+998977777777", sender=666, owner=666, chat=6))
    assert await poll(client, t2) == "mismatch"
    assert await poll(client, "yoq-token-1234") == "expired"


async def test_contact_without_reset_request_and_admin_gets_no_session(client):
    from app.cli import create_admin

    r = await hook(client, contact_msg("+998901112233", chat=77))
    assert r.status_code == 200  # so'rovsiz kontakt: "eskirgan" javobi, xato emas

    await create_admin("+998909998877", "juda-kuchli-parol-123")
    token = await start_reset(client, phone="+998909998877")
    await hook(client, contact_msg("+998909998877"))
    assert await poll(client, token) == "verified"
    done = await client.post("/v1/auth/password-reset/complete", json={"token": token, "new_password": "yangi-admin-parol-1"})
    assert done.status_code == 200 and done.json()["session"] is None  # admin TOTP bilan kiradi
    r = await client.post("/v1/auth/login", json={"phone": "+998909998877", "password": "yangi-admin-parol-1"})
    assert r.json()["error"]["code"] == "totp_required"


async def test_reset_clears_login_lock(client):
    from app.core.redis import get_redis

    await register(client, PHONE, "eski-parol-123")
    await get_redis().set(f"login_fail:{PHONE}", 10)
    token = await start_reset(client)
    await hook(client, contact_msg(PHONE))
    await client.post("/v1/auth/password-reset/complete", json={"token": token, "new_password": "yangi-parol-123"})
    assert (await client.post("/v1/auth/login", json={"phone": PHONE, "password": "yangi-parol-123"})).status_code == 200
