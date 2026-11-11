"""Sayt va Telegram yordamchisi: faktlar bazadan, katalog qidiruvi, provayder zaxirasi, Aloqa belgisi, cheklovlar."""
from types import SimpleNamespace

import httpx
import pytest

from app.ai.providers import Completion
from app.core.config import get_settings
from tests.conftest import auth, register


class FakeProvider:
    def __init__(self, name, text=None, fail=False):
        self.name, self.text, self.fail, self.calls = name, text, fail, []

    async def chat(self, client, system, messages, max_tokens=2000, temperature=0.7):
        self.calls.append({"system": system, "messages": messages, "max_tokens": max_tokens})
        if self.fail:
            raise httpx.ConnectError("down")
        return Completion(self.text, 50, self.name)


@pytest.fixture
def providers(monkeypatch):
    monkeypatch.setattr(get_settings(), "ai_enabled", True)

    def use(*items):
        monkeypatch.setattr("app.assistant.service.ordered_providers", lambda: list(items))
        return items
    return use


@pytest.fixture(autouse=True)
def frozen_clock(monkeypatch):
    import app.core.ratelimit as rl
    monkeypatch.setattr(rl, "time", SimpleNamespace(time=lambda: 1_800_000_000.0))


def ask(client, *texts, headers=None):
    msgs = [{"role": "user" if i % 2 == 0 else "assistant", "content": t} for i, t in enumerate(texts)]
    return client.post("/v1/assistant/chat", json={"messages": msgs}, headers=headers or {})


async def test_reply_uses_live_facts_catalog_and_fallback_provider(client, providers):
    down, ok = providers(FakeProvider("openai", fail=True),
                         FakeProvider("gemini", "Ha, asalchilik bo'yicha tayyor reja bor. Narxi kartochkada."))
    r = await ask(client, "Salom", "Assalomu alaykum! Qanday yordam beray?", "Asalchilik biznes rejasi bormi?")
    body = r.json()
    assert r.status_code == 200 and body["reply"].startswith("Ha, asalchilik") and body["handoff"] is False
    assert body["products"] and all("asal" in p["title"].lower() for p in body["products"])
    assert len(down.calls) == 1 and len(ok.calls) == 1  # birinchisi yiqildi, keyingisi javob berdi
    system = ok.calls[0]["system"]
    assert "Standart: 200 000 so'm / 30 kun" in system and "Bepul: bepul" in system  # tariflar bazadan
    assert "Obunasiz bitta reja" in system and "Katalogda 269 ta" in system and "Click" in system
    assert [m["role"] for m in ok.calls[0]["messages"]] == ["user", "assistant", "user"]


async def test_handoff_marker_is_stripped(client, providers):
    providers(FakeProvider("openai", "Uzr, to'lov holatini admin tekshiradi. [ALOQA]"))
    body = (await ask(client, "Pul yechildi, lekin reja ochilmadi")).json()
    assert body["handoff"] is True and "[ALOQA]" not in body["reply"]


async def test_without_ai_gives_contact_fallback(client):
    body = (await ask(client, "Tariflar qancha?")).json()  # testlarda AI o'chiq
    assert body["handoff"] is True and "Aloqa" in body["reply"]


async def test_validation_and_guest_rate_limit(client, providers):
    providers(FakeProvider("openai", "Javob"))
    assert (await client.post("/v1/assistant/chat", json={"messages": []})).status_code == 422
    assert (await ask(client, "savol", "javob")).status_code == 422          # oxirgi xabar foydalanuvchidan emas
    assert (await ask(client, "x" * 1001)).status_code == 422                # juda uzun savol
    codes = [(await ask(client, f"savol {i}")).status_code for i in range(16)]
    assert codes[:12].count(200) == 12 and codes[-1] == 429
    token = await register(client)
    assert (await ask(client, "kirgan foydalanuvchi", headers=auth(token))).status_code == 200  # alohida chegara


async def test_telegram_text_goes_to_assistant_with_safe_html(client, providers, monkeypatch):
    sent = []

    async def fake_send(chat_id, text, reply_markup=None):
        sent.append(text)

    async def no_action(chat_id, action="typing"):
        return None

    monkeypatch.setattr("app.modules.telegram.assistant.send_message", fake_send)
    monkeypatch.setattr("app.modules.telegram.assistant.send_chat_action", no_action)
    prov, = providers(FakeProvider("openai", "Asal <b>reja</b> bor & arzon"))
    hook = {"X-Telegram-Bot-Api-Secret-Token": get_settings().telegram_webhook_header_token}
    msg = {"chat": {"id": 42}, "from": {"id": 42, "first_name": "Ali"}}
    r = await client.post("/v1/telegram/webhook", json={"message": {**msg, "text": "Asalchilik rejasi bormi?"}}, headers=hook)
    assert r.status_code == 200 and len(sent) == 1
    assert "Asal &lt;b&gt;reja&lt;/b&gt; bor &amp; arzon" in sent[0] and '<a href="http://' in sent[0]
    await client.post("/v1/telegram/webhook", json={"message": {**msg, "text": "Narxi qancha?"}}, headers=hook)
    assert [m["role"] for m in prov.calls[1]["messages"]] == ["user", "assistant", "user"]  # tarix saqlangan
    await client.post("/v1/telegram/webhook", json={"message": {**msg, "text": "/help"}}, headers=hook)
    assert len(prov.calls) == 2  # buyruqlar yordamchiga bormaydi


async def test_catalog_search_tolerates_suffixes(client):
    from app.assistant.service import find_products
    from app.db.session import sessionmaker

    async with sessionmaker()() as s:
        found = [p.title for p in await find_products(s, "Baliqchilik bo'yicha tayyor reja bormi?")]
        assert any("baliqchilik" in t.lower() for t in found) and any("baliqlar" in t.lower() for t in found)
        assert found[0].lower().count("baliqchilik") == 1  # aniqroq mos birinchi
        assert await find_products(s, "salom, qanday?") == []
