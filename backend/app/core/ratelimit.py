"""Redis asosidagi rate limit: barcha server nusxalari uchun umumiy."""
import time

from fastapi import Request

from app.core.errors import AppError
from app.core.redis import get_redis


def client_ip(request: Request) -> str:
    # uvicorn --proxy-headers Render proksisidan haqiqiy IP ni request.client ga qo'yadi
    return request.client.host if request.client else "unknown"


def rate_limit(name: str, limit: int, window_seconds: int):
    async def dependency(request: Request) -> None:
        bucket = int(time.time()) // window_seconds
        key = f"rl:{name}:{client_ip(request)}:{bucket}"
        r = get_redis()
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, window_seconds + 1)
        if count > limit:
            raise AppError(429, "rate_limited", "Juda ko'p so'rov. Birozdan so'ng qayta urinib ko'ring.")

    return dependency
