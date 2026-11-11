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
    "PDF_ENABLED": "false",  # LibreOffice faqat tests/test_plan_pdf.py da (tez va muhitga bog'liq emas)
    "PEXELS_API_KEY": "", "PIXABAY_API_KEY": "",  # lokal .env dagi haqiqiy kalitlar testlarga ta'sir qilmasin
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
    import shutil  # lokal fayl saqlash ham har test uchun toza (bir test qo'ygan PDF boshqasiga ta'sir qilmasin)
    shutil.rmtree(os.environ["LOCAL_STORAGE_DIR"], ignore_errors=True)
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


async def register(client, phone="+998901112233", password="parol12345", credits=0):
    """credits: bir martalik reja kreditlari (2026-11-12 dan bepul tarifda hujjat yo'q, reja yaratish uchun kerak)."""
    r = await client.post("/v1/auth/register", json={"phone": phone, "password": password, "first_name": "Test"})
    assert r.status_code == 201, r.text
    if credits:
        from sqlalchemy import update

        from app.db.session import sessionmaker
        from app.models import User

        async with sessionmaker()() as s:
            await s.execute(update(User).where(User.phone == phone).values(plan_credits=credits))
            await s.commit()
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


PLAN_INPUT = {
    "faoliyat_turi": "ishlab_chiqarish", "loyiha_nomi": "Non sexi", "tashabbuskor": "Baraka MCHJ",
    "loyiha_qiymati": 150_000_000, "oz_mablag": 50_000_000, "kredit": 100_000_000, "foiz": 14, "muddat": 36,
    "imtiyoz": 6, "hajm": 2500, "narx": 120000, "direktor": 1, "rahbar_oylik": 5_000_000, "xodim": 4,
    "ishchi_oylik": 3_500_000,
}


async def put_catalog_pdf(product_id: str) -> None:
    """Katalog rejasining PDF faylini saqlashga qo'yadi (fayli yo'q reja sotilmaydi)."""
    from app.db.session import sessionmaker
    from app.models import CatalogProduct
    from app.storage import get_storage

    async with sessionmaker()() as s:
        key = (await s.get(CatalogProduct, product_id)).file_key
    await get_storage().put_bytes(key, b"%PDF-1.4 test", "application/pdf")


async def remove_catalog_pdf(product_id: str) -> None:
    """Lokal saqlashdan katalog PDF'ini o'chiradi (fayl yo'qolgan holatni sinash uchun)."""
    import os

    from app.db.session import sessionmaker
    from app.models import CatalogProduct
    from app.storage import get_storage

    async with sessionmaker()() as s:
        key = (await s.get(CatalogProduct, product_id)).file_key
    path = get_storage().path_for(key)
    if os.path.exists(path):
        os.remove(path)
