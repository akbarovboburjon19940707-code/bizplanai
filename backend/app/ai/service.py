"""AI bo'limlarini parallel yaratish. Kalit yo'q, byudjet tugagan yoki provayder ishlamasa: bo'sh natija
(hujjat shablon matnlari bilan baribir tayyorlanadi)."""
import asyncio
import logging

import httpx

from app.ai.prompts import SECTIONS, SYSTEM, build_prompt
from app.ai.providers import Provider, configured_providers
from app.core.config import get_settings
from app.core.redis import get_redis
from app.core.security import utcnow

log = logging.getLogger(__name__)
MIN_WORDS = 120


def ai_available() -> bool:
    s = get_settings()
    return s.ai_enabled and bool(configured_providers(s))


async def _budget_left() -> bool:
    used = int(await get_redis().get(f"ai:tokens:{utcnow():%Y-%m-%d}") or 0)
    return used < get_settings().ai_daily_token_budget


async def _record(tokens: int) -> None:
    key = f"ai:tokens:{utcnow():%Y-%m-%d}"
    r = get_redis()
    await r.incrby(key, max(tokens, 1))
    await r.expire(key, 2 * 86400)


async def _one(client: httpx.AsyncClient, providers: list[Provider], prompt: str) -> tuple[str | None, str | None]:
    for p in providers:
        if not await _budget_left():
            log.warning("AI kunlik token byudjeti tugadi")
            return None, None
        try:
            c = await p.complete(client, SYSTEM, prompt)
            await _record(c.tokens or len(c.text.split()) * 3)
            if len(c.text.split()) >= MIN_WORDS:
                return c.text.strip(), c.provider
            log.warning("AI javobi qisqa: provider=%s", p.name)
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            log.warning("AI provider xatosi: provider=%s err=%s", p.name, exc)
    return None, None


async def generate_sections(ctx: dict, indicators: dict) -> dict[str, dict]:
    """{"bozor_tahlili": {"title": ..., "text": ..., "provider": ...}, ...}"""
    s = get_settings()
    providers = configured_providers(s)
    if not s.ai_enabled or not providers:
        return {}
    async with httpx.AsyncClient(timeout=s.ai_timeout_seconds) as client:
        results = await asyncio.gather(*[_one(client, providers, build_prompt(topic, ctx, indicators))
                                         for _, _, topic in SECTIONS])
    out = {}
    for (key, title, _), (text, provider) in zip(SECTIONS, results, strict=True):
        if text:
            out[key] = {"title": title, "text": text, "provider": provider}
    return out
