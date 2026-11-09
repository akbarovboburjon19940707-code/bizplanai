"""Redis ulanishi. Dev/test rejimida REDIS_URL bo'lmasa xotiradagi fakeredis ishlatiladi."""
from redis.asyncio import Redis

from app.core.config import get_settings

_client: Redis | None = None


def get_redis() -> Redis:
    global _client
    if _client is None:
        url = get_settings().redis_url
        if url:
            _client = Redis.from_url(url, decode_responses=True)
        else:
            import fakeredis

            _client = fakeredis.FakeAsyncRedis(decode_responses=True)
    return _client


def set_redis(client: Redis | None) -> None:
    global _client
    _client = client
