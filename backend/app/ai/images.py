"""Biznes-reja muqovasi uchun rasm: foydalanuvchi yuklagan yoki faoliyat turiga qarab avtomatik (Pexels yoki Pixabay).

Avtomatik rasm: AI loyiha nomi va mahsulotdan 2-4 ta inglizcha qidiruv so'zi tuzadi (AI bo'lmasa faoliyat turi
bo'yicha tayyor so'zlar), Pexels yoki Pixabay API dan landscape rasm olinadi. Ikkala kalit ham bo'lmasa o'chiq.
Pexels 2026-11 holatiga yangi kalit bermayapti, shuning uchun Pixabay qo'shilgan.
Pexels litsenziyasi rasmlarni bepul va tijoriy maqsadda ishlatishga ruxsat beradi; Pexels API qoidalari esa
Pexels va fotografni ko'rsatishni so'raydi, shuning uchun rasm ostiga "Foto: <fotograf> / Pexels" yoziladi.
Tashqi xizmatga faqat qidiruv so'zlari ketadi (shaxsiy ma'lumot emas).
"""
import logging
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings

log = logging.getLogger(__name__)

PEXELS_SEARCH = "https://api.pexels.com/v1/search"
PIXABAY_SEARCH = "https://pixabay.com/api/"
PEXELS_HOSTS = ("images.pexels.com",)
PIXABAY_HOSTS = ("pixabay.com", "cdn.pixabay.com")
FALLBACK_QUERY = {
    "ishlab_chiqarish": "factory production workshop",
    "qishloq_xojaligi": "farm agriculture field",
    "savdo": "grocery store shop shelves",
    "xizmat": "small business service workplace",
}


@dataclass
class CoverImage:
    data: bytes
    credit: str | None = None  # avtomatik rasm uchun muallif yozuvi


_MAGIC = {b"\xff\xd8\xff": ("jpg", "image/jpeg"), b"\x89PNG\r\n\x1a\n": ("png", "image/png")}


def sniff_image(data: bytes) -> tuple[str, str] | None:
    """Faqat JPG va PNG (Word ikkalasini ham qo'llaydi). (kengaytma, MIME) yoki None."""
    return next((v for magic, v in _MAGIC.items() if data.startswith(magic)), None)


def _clean_query(text: str) -> str | None:
    line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    words = re.findall(r"[A-Za-z]+", line)[:5]
    return " ".join(words).lower() if len(words) >= 1 else None


async def _ai_query(ctx: dict) -> str | None:
    """AI orqali inglizcha qidiruv so'zlari. AI o'chiq yoki xato bo'lsa None."""
    from app.ai.providers import configured_providers

    s = get_settings()
    providers = configured_providers(s)
    if not s.ai_enabled or not providers:
        return None
    prompt = (
        "Give 2 to 4 English keywords for a stock photo that illustrates this small business. "
        "Answer with the keywords only, separated by spaces, no punctuation.\n"
        f"Business: {ctx.get('loyiha_nomi') or ''}. Products: {ctx.get('mahsulot') or ''}. "
        f"Activity: {ctx.get('faoliyat_turi_nomi') or ''}."
    )
    async with httpx.AsyncClient(timeout=20) as client:
        for p in providers:
            try:
                c = await p.complete(client, "You write short English stock photo search queries.", prompt)
                q = _clean_query(c.text)
                if q:
                    return q
            except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
                log.warning("AI rasm so'rovi xatosi: provider=%s err=%s", p.name, exc)
    return None


async def _download(client: httpx.AsyncClient, url: str, max_bytes: int, hosts: tuple[str, ...]) -> bytes | None:
    if urlparse(url).hostname not in hosts or urlparse(url).scheme != "https":
        return None
    async with client.stream("GET", url) as r:
        if r.status_code != 200:
            return None
        data = b""
        async for chunk in r.aiter_bytes():
            data += chunk
            if len(data) > max_bytes:
                return None
    return data if sniff_image(data) else None


def _credit(name: object, source: str) -> str:
    name = re.sub(r"\s+", " ", str(name or "")).strip()[:80]
    return f"Foto: {name} / {source}" if name else f"Foto: {source}"


async def _from_pexels(client: httpx.AsyncClient, key: str, query: str, max_bytes: int) -> CoverImage | None:
    r = await client.get(PEXELS_SEARCH, headers={"Authorization": key},
                         params={"query": query, "orientation": "landscape", "per_page": 5, "size": "medium"})
    if r.status_code != 200:
        log.warning("Pexels javobi: %s", r.status_code)
        return None
    for photo in r.json().get("photos", []):
        url = (photo.get("src") or {}).get("large")
        data = await _download(client, url, max_bytes, PEXELS_HOSTS) if url else None
        if data:
            return CoverImage(data, _credit(photo.get("photographer"), "Pexels"))
    return None


async def _from_pixabay(client: httpx.AsyncClient, key: str, query: str, max_bytes: int) -> CoverImage | None:
    """Pixabay: rasm yuklab olinib hujjatga joylanadi (hotlink emas); Content License tijoriy foydalanishga ruxsat beradi."""
    r = await client.get(PIXABAY_SEARCH, params={"key": key, "q": query[:100], "image_type": "photo",
                                                 "orientation": "horizontal", "safesearch": "true", "per_page": 5})
    if r.status_code != 200:
        log.warning("Pixabay javobi: %s", r.status_code)
        return None
    for hit in r.json().get("hits", []):
        url = hit.get("largeImageURL") or hit.get("webformatURL")
        data = await _download(client, url, max_bytes, PIXABAY_HOSTS) if url else None
        if data:
            return CoverImage(data, _credit(hit.get("user"), "Pixabay"))
    return None


async def fetch_cover_image(ctx: dict) -> CoverImage | None:
    """Faoliyat turiga mos muqova rasmi yoki None (kalit yo'q, topilmadi, tarmoq xatosi).
    Manbalar tartibi: Pexels (PEXELS_API_KEY), keyin Pixabay (PIXABAY_API_KEY); qaysi kalit bo'lsa o'sha ishlaydi."""
    s = get_settings()
    sources = [(fn, key) for fn, key in ((_from_pexels, s.pexels_api_key), (_from_pixabay, s.pixabay_api_key)) if key]
    if not sources:
        return None
    query = await _ai_query(ctx) or FALLBACK_QUERY.get(ctx.get("faoliyat_turi") or "", FALLBACK_QUERY["xizmat"])
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        for fn, key in sources:
            try:
                cover = await fn(client, key, query, s.max_plan_image_bytes)
                if cover:
                    return cover
            except (httpx.HTTPError, ValueError) as exc:
                log.warning("Muqova rasmini olib bo'lmadi (%s): %s", fn.__name__, exc)
    return None
