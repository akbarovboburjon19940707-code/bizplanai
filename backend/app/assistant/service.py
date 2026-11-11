"""Sayt va Telegram yordamchisi. Bir xil mantiq: tarix (oxirgi 10 xabar) + bazadan faktlar + mos katalog rejalari ->
LLM (provayderlar navbat bilan). AI yo'q, byudjet tugagan yoki hamma provayder xato bersa: zaxira javob (Aloqa)."""
import logging
import re
from dataclasses import dataclass, field

import httpx
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers import Message, Provider, configured_providers
from app.assistant.knowledge import HANDOFF, facts, system_prompt
from app.core.config import get_settings
from app.core.redis import get_redis
from app.core.security import utcnow
from app.models import CatalogProduct
from app.modules.payments.service import enabled_providers

log = logging.getLogger(__name__)

MAX_TURNS = 10
MAX_MESSAGE_CHARS = 1000
# Katalog qidiruvida ma'no bermaydigan umumiy so'zlar (savol so'zlari, "tayyor reja" va h.k.)
STOP_WORDS = {"biznes", "reja", "rejasi", "rejani", "rejalar", "rejangiz", "bormi", "kerak", "uchun", "qanday", "qancha",
              "narxi", "plan", "tayyor", "bo'yicha", "boʻyicha", "bo‘yicha", "boyicha", "haqida", "loyiha", "loyihasi",
              "loyihani", "sotib", "olish", "olsam", "bersangiz", "bering", "ayting", "iltimos", "yordam", "salom",
              "assalomu", "alaykum", "menga", "sizda", "sizlarda", "qayerdan", "topsam", "бизнес", "план", "нужен",
              "сколько", "готовый", "есть", "ассалому", "алайкум", "керак", "борми", "тайёр", "бўйича"}
FALLBACK = ("Hozir yordamchi javob bera olmayapti. Savolingizni Aloqa sahifasidagi forma orqali yuboring yoki "
            "Telegram orqali yozing: tez orada javob beramiz.")


@dataclass
class Reply:
    text: str
    products: list[CatalogProduct] = field(default_factory=list)
    handoff: bool = False
    provider: str | None = None


def ordered_providers() -> list[Provider]:
    s = get_settings()
    by_name = {p.name: p for p in configured_providers(s)}
    order = [n.strip() for n in s.assistant_providers.split(",") if n.strip()]
    return [by_name[n] for n in order if n in by_name] + [p for n, p in by_name.items() if n not in order]


def _keywords(text: str) -> list[str]:
    words = re.findall(r"[\w'ʻʼ‘’-]{4,}", text.lower())
    out = []
    for w in words:
        w = w.strip("'ʻʼ‘’-")
        if len(w) >= 4 and w not in STOP_WORDS and w not in out:
            out.append(w)
    return out[:6]


async def find_products(session: AsyncSession, text: str, limit: int = 4) -> list[CatalogProduct]:
    """Oddiy kalit so'z qidiruvi (ILIKE), o'zbekcha qo'shimchalarga chidamli: topish uchun so'z boshi (5 harf,
    "baliqchilik" -> "baliq", shunda "baliqlar" ham topiladi), tartiblash uchun uzunroq o'zak ("baliqchil")."""
    words = _keywords(text)
    if not words:
        return []
    stems = [w[:-2] if len(w) > 6 else w for w in words]
    prefixes = sorted({w[:5] for w in words})
    rows = list(await session.scalars(select(CatalogProduct).where(
        CatalogProduct.is_active.is_(True), or_(*[CatalogProduct.title.ilike(f"%{x}%") for x in prefixes])).limit(80)))

    def score(p: CatalogProduct) -> int:
        title = p.title.lower()
        return 2 * sum(st in title for st in stems) + sum(x in title for x in prefixes)

    rows.sort(key=lambda p: (-score(p), -p.downloads, p.title))
    return rows[:limit]


def clean_history(messages: list[dict]) -> list[Message]:
    out: list[Message] = []
    for m in messages[-MAX_TURNS:]:
        role = "assistant" if m.get("role") == "assistant" else "user"
        content = str(m.get("content") or "").strip()[:MAX_MESSAGE_CHARS]
        if content:
            out.append({"role": role, "content": content})
    while out and out[0]["role"] != "user":  # provayderlar suhbat foydalanuvchidan boshlanishini kutadi
        out.pop(0)
    return out


async def _budget_ok() -> bool:
    used = int(await get_redis().get(f"assistant:tokens:{utcnow():%Y-%m-%d}") or 0)
    return used < get_settings().assistant_daily_token_budget


async def _record(tokens: int) -> None:
    r = get_redis()
    key = f"assistant:tokens:{utcnow():%Y-%m-%d}"
    await r.incrby(key, max(tokens, 1))
    await r.expire(key, 2 * 86400)


async def answer(session: AsyncSession, history: list[dict]) -> Reply:
    messages = clean_history(history)
    if not messages or messages[-1]["role"] != "user":
        return Reply(FALLBACK, handoff=True)
    products = await find_products(session, messages[-1]["content"])
    s = get_settings()
    providers = ordered_providers()
    if not (s.assistant_enabled and s.ai_enabled and providers) or not await _budget_ok():
        return Reply(FALLBACK, products, handoff=True)
    system = system_prompt(await facts(session, enabled_providers()), products)
    async with httpx.AsyncClient(timeout=min(s.ai_timeout_seconds, 30)) as client:
        for p in providers:
            try:
                c = await p.chat(client, system, messages, max_tokens=s.assistant_max_reply_tokens, temperature=0.3)
            except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
                log.warning("yordamchi: provider xatosi provider=%s err=%s", p.name, exc)
                continue
            await _record(c.tokens or len(c.text.split()) * 3)
            text = c.text.strip()
            if not text:
                continue
            handoff = HANDOFF in text
            text = text.replace(HANDOFF, "").strip()
            return Reply(text or FALLBACK, products, handoff, c.provider)
    return Reply(FALLBACK, products, handoff=True)
