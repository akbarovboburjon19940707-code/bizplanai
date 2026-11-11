"""Redis asosidagi rate limit: barcha server nusxalari uchun umumiy."""
import hmac
import time

from fastapi import Request

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.redis import get_redis


def client_ip(request: Request) -> str:
    # uvicorn --proxy-headers Render proksisidan haqiqiy IP ni request.client ga qo'yadi
    return request.client.host if request.client else "unknown"


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
