"""Aloqa formasi: murojaat saqlanadi, adminga Telegram xabari (HTML escape), spam himoyasi, admin ro'yxati."""
from sqlalchemy import func, select

from tests.conftest import auth, register

GOOD = {"name": "Aziz  Karimov", "phone": "90 123 45 67", "topic": "payment",
        "message": "Click orqali to'ladim, lekin reja ochilmadi. <b>Yordam</b> bering."}


async def _admin_headers():
    from app.cli import create_admin
    from app.core.security import create_access_token
    from app.db.session import sessionmaker
    from app.models import User

    await create_admin("+998909998877", "juda-kuchli-parol-123")
    async with sessionmaker()() as s:
        admin = (await s.scalars(select(User).where(User.role == "admin"))).one()
    return auth(create_access_token(admin.id, "admin"))


async def test_contact_message_saved_and_admin_notified(client, monkeypatch):
    sent = []

    async def fake_notify(text):
        sent.append(text)

    monkeypatch.setattr("app.modules.contact.router.notify_admin", fake_notify)
    token = await register(client)
    r = await client.post("/v1/contact", json=GOOD, headers=auth(token))
    assert r.status_code == 201 and r.json()["status"] == "new"
    assert len(sent) == 1
    assert "&lt;b&gt;Yordam&lt;/b&gt;" in sent[0] and "<b>Yordam</b>" not in sent[0]  # foydalanuvchi matni escape
    assert "+998901234567" in sent[0] and "To'lov" in sent[0] and "ro'yxatdan o'tgan" in sent[0]

    # bir daqiqa ichida o'sha raqamdan takroriy xabar qabul qilinmaydi
    again = await client.post("/v1/contact", json=GOOD)
    assert again.status_code == 429

    admin = await _admin_headers()
    stats = (await client.get("/v1/admin/stats", headers=admin)).json()
    assert stats["messages_new"] == 1
    rows = (await client.get("/v1/admin/messages", params={"status": "new"}, headers=admin)).json()
    assert len(rows) == 1 and rows[0]["name"] == "Aziz Karimov" and rows[0]["phone"] == "+998901234567"
    assert rows[0]["user_id"] is not None
    done = await client.post(f"/v1/admin/messages/{rows[0]['id']}/done", json={"note": "qo'ng'iroq qilindi"}, headers=admin)
    assert done.json()["status"] == "done" and done.json()["admin_note"] == "qo'ng'iroq qilindi"
    assert (await client.get("/v1/admin/messages", params={"status": "new"}, headers=admin)).json() == []
    assert (await client.post("/v1/admin/messages/yoq/done", json={}, headers=admin)).status_code == 404
    # oddiy foydalanuvchi ro'yxatni ko'ra olmaydi
    assert (await client.get("/v1/admin/messages", headers=auth(token))).status_code == 403


async def test_contact_validation_and_honeypot(client, monkeypatch):
    from app.db.session import sessionmaker
    from app.models import ContactMessage

    sent = []

    async def fake_notify(text):
        sent.append(text)

    monkeypatch.setattr("app.modules.contact.router.notify_admin", fake_notify)
    assert (await client.post("/v1/contact", json={**GOOD, "phone": "123"})).status_code == 422
    assert (await client.post("/v1/contact", json={**GOOD, "message": "qisqa"})).status_code == 422
    assert (await client.post("/v1/contact", json={**GOOD, "name": " "})).status_code == 422
    assert (await client.post("/v1/contact", json={**GOOD, "topic": "spam"})).status_code == 422
    bot = await client.post("/v1/contact", json={**GOOD, "phone": "901111111", "website": "http://spam"})
    assert bot.status_code == 201  # bot muvaffaqiyat ko'radi, lekin hech narsa saqlanmaydi
    async with sessionmaker()() as s:
        assert await s.scalar(select(func.count()).select_from(ContactMessage)) == 0
    assert sent == []
