import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ.update({
    "APP_ENV": "test", "DATABASE_URL": os.environ.get("TEST_DATABASE_URL", f"sqlite+aiosqlite:///{_tmp}/test.db"), "JOB_MODE": "inline",
    "STORAGE_BACKEND": "local", "LOCAL_STORAGE_DIR": f"{_tmp}/storage", "PUBLIC_API_URL": "http://test",
    "TELEGRAM_BOT_TOKEN": "123456:TEST-TOKEN", "TELEGRAM_WEBHOOK_SECRET": "hook-secret",
    "CLICK_SERVICE_ID": "11111", "CLICK_MERCHANT_ID": "22222", "CLICK_SECRET_KEY": "click-secret",
    "PAYME_MERCHANT_ID": "payme-merchant", "PAYME_SECRET_KEY": "payme-key",
    "MANUAL_CARD_NUMBER": "8600 0000 0000 0000", "AI_ENABLED": "false",
})

import fakeredis  # noqa: E402
import httpx  # noqa: E402
import pytest  # noqa: E402

import app.models  # noqa: E402,F401
from app.cli import seed  # noqa: E402
from app.core.redis import set_redis  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import dispose_engine, get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.storage import set_storage  # noqa: E402


@pytest.fixture(autouse=True)
async def fresh_state():
    set_redis(fakeredis.FakeAsyncRedis(decode_responses=True))
    set_storage(None)
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed(25000)
    yield
    await dispose_engine()


@pytest.fixture
async def client():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def register(client, phone="+998901112233", password="parol12345"):
    r = await client.post("/v1/auth/register", json={"phone": phone, "password": password, "first_name": "Test"})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


PLAN_INPUT = {
    "faoliyat_turi": "ishlab_chiqarish", "loyiha_nomi": "Non sexi", "tashabbuskor": "Baraka MCHJ",
    "loyiha_qiymati": 150_000_000, "oz_mablag": 50_000_000, "kredit": 100_000_000, "foiz": 14, "muddat": 36,
    "imtiyoz": 6, "hajm": 2500, "narx": 120000, "direktor": 1, "rahbar_oylik": 5_000_000, "xodim": 4,
    "ishchi_oylik": 3_500_000,
}
