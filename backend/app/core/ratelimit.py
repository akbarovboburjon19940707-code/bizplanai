"""Redis asosidagi rate limit: barcha server nusxalari uchun umumiy."""
import hmac
import time

from fastapi import Request

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.redis import get_redis


def client_ip(request: Request) -> str:
    """Rate limit uchun mijoz IP si. Manba sozlamada (CLIENT_IP_SOURCE): mijoz o'zi yozib yubora oladigan qiymatga
    ishonilmasligi kerak, aks holda har so'rovda boshqa "IP" bilan cheklovlar chetlab o'tiladi."""
    source = get_settings().client_ip_source
    fallback = request.client.host if request.client else "unknown"
    if source.startswith("header:"):
        value = request.headers.get(source[len("header:"):].strip(), "").split(",")[0].strip()
        return value or fallback
    if source == "xff_last":
        hops = [h.strip() for h in request.headers.get("x-forwarded-for", "").split(",") if h.strip()]
        return hops[-1] if hops else fallback
    return fallback  # xff_first: uvicorn --proxy-headers natijasi


def _is_loadtest(request: Request) -> bool:
    """Staging yuklama testi (k6, bitta IP): LOADTEST_TOKEN berilgan va sarlavha mos bo'lsa rate limit yo'q."""
    token = get_settings().loadtest_token
    sent = request.headers.get("x-loadtest-token", "")
    return len(token) >= 32 and bool(sent) and hmac.compare_digest(sent, token)


def rate_limit(name: str, limit: int, window_seconds: int):
    async def dependency(request: Request) -> None:
        if _is_loadtest(request):
            return
        bucket = int(time.time()) // window_seconds
        key = f"rl:{name}:{client_ip(request)}:{bucket}"
        r = get_redis()
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, window_seconds + 1)
        if count > limit:
            raise AppError(429, "rate_limited", "Juda ko'p so'rov. Birozdan so'ng qayta urinib ko'ring.")

    return dependency


async def hit(key: str, limit: int, window_seconds: int, message: str | None = None) -> None:
    """Istalgan kalit bo'yicha cheklov (foydalanuvchi id, Telegram chat va h.k.); oshsa 429."""
    bucket = int(time.time()) // window_seconds
    r = get_redis()
    full = f"rl:{key}:{bucket}"
    count = await r.incr(full)
    if count == 1:
        await r.expire(full, window_seconds + 1)
    if count > limit:
        raise AppError(429, "rate_limited", message or "Juda ko'p so'rov. Birozdan so'ng qayta urinib ko'ring.")
