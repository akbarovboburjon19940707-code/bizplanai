"""Eski sayt (Flask) bazasidan ko'chirish va Werkzeug parol xeshlari."""
import sqlite3
from datetime import datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.core.security import needs_rehash, verify_password
from tests.conftest import register

# Haqiqiy werkzeug 3.1 generate_password_hash("eski-parol-123", method=...) natijalari
WERKZEUG = {
    "scrypt": "scrypt:32768:8:1$WhF0xVc6yU2FxUGg$2b8253c6966d7552d5786122c0e657fe6788b8cac5bb1ef8f61ea90a2986bb05ededbdc042abb9b7805c57a75555e56ee17b9e9d6986a68b7cb53e9aae89d831",
    "pbkdf2_sha256_1m": "pbkdf2:sha256:1000000$FHVskSM8xsnGWiAW$4f27bb6406e69528c5159cc50f71ec4e136b8c878ee0123a5d7eef1f4cca38bb",
    "pbkdf2_sha256_260k": "pbkdf2:sha256:260000$LpOxi9wK8s310Xg6$364b7f3f5af06b94f242b0e9efcce50a19428b6575ef653455a3b7be26041bec",
    "pbkdf2_sha1": "pbkdf2:sha1:1000$7JKccscZrocjwtnY$6e48a8809248f4c732a5cc5871e9d98678ace7b7",
}


@pytest.mark.parametrize("name", WERKZEUG)
def test_werkzeug_hashes_verify(name):
    stored = WERKZEUG[name]
    assert verify_password("eski-parol-123", stored)
    assert not verify_password("eski-parol-124", stored)
    assert needs_rehash(stored)


def test_bad_legacy_hashes_are_rejected():
    for stored in ("plain$text", "pbkdf2:md5:1000$salt$abcd", "bcrypt$x$y", "scrypt:1:1$", ""):
        assert not verify_password("x", stored)


def _legacy_db(path, products: list[str]) -> str:
    future, past = datetime.now() + timedelta(days=20), datetime.now() - timedelta(days=5)
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE users (id TEXT PRIMARY KEY, phone TEXT, first_name TEXT, last_name TEXT, telegram_id TEXT,
            telegram_username TEXT, password_hash TEXT, role TEXT, is_active BOOLEAN, created_at DATETIME);
        CREATE TABLE subscriptions (id INTEGER PRIMARY KEY, user_id TEXT, plan_name TEXT, status TEXT,
            start_date DATETIME, end_date DATETIME, payment_id TEXT);
        CREATE TABLE payments (id INTEGER PRIMARY KEY, user_name TEXT, payment_status TEXT, payment_type TEXT,
            loyiha_nomi TEXT, amount NUMERIC, created_at DATETIME);
    """)
    users = [
        ("u-aziz1", "+998901112200", "Aziz", "", None, None, WERKZEUG["scrypt"], "premium", 1),
        ("u-tg", "tg_555", "TG_555", "", "555", "tg_user", WERKZEUG["pbkdf2_sha1"], "user", 1),
        ("u-aziz2", "901112211", "Aziz", "", None, None, WERKZEUG["pbkdf2_sha256_260k"], "user", 1),
        ("u-bad", "12345", "Bad", "", None, None, WERKZEUG["scrypt"], "user", 1),
        ("u-exists", "+998901119988", "Mavjud", "", None, None, WERKZEUG["scrypt"], "user", 1),
        ("u-admin", "+998901110001", "Eski admin", "", None, None, WERKZEUG["scrypt"], "admin", 1),
    ]
    c.executemany("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,'2025-01-02 10:00:00')", users)
    c.executemany("INSERT INTO subscriptions VALUES (?,?,?,?,?,?,?)", [
        (1, "u-aziz1", "pro", "active", past, future, "p1"),        # ko'chadi
        (2, "u-tg", "enterprise", "active", past, past, "p2"),      # muddati tugagan
        (3, "u-aziz2", "basic", "active", past, future, None),      # bepul
        (4, "u-bad", "pro", "active", past, future, "p4"),          # egasi ko'chmagan
    ])
    c.executemany("INSERT INTO payments VALUES (?,?,?,?,?,?, '2025-03-01')", [
        (1, "+998901112200", "success", "catalog", products[0], 25000),   # telefon bo'yicha: aniq
        (2, "Aziz", "success", "catalog", products[1], 25000),            # 2 ta Aziz: tekshirish
        (3, "TG_555", "success", "catalog", products[1], 25000),          # yagona ism: aniq
        (4, "+998901112200", "success", "catalog", "Bunday reja yo'q", 1), # reja topilmadi
        (5, "+998901112200", "pending", "catalog", products[2], 1),       # to'lanmagan
        (6, "+998901112200", "success", "subscription", "", 50000),       # katalog emas
    ])
    c.commit()
    c.close()
    return f"sqlite+aiosqlite:///{path}"


async def test_import_legacy_dry_run_apply_and_rerun(client, tmp_path):
    from app.db.session import sessionmaker
    from app.legacy_import import read_source, run_import
    from app.models import CatalogProduct, Entitlement, Subscription, User

    await register(client, phone="+998901119988")  # yangi saytda allaqachon bor
    async with sessionmaker()() as s:
        titles = list(await s.scalars(select(CatalogProduct.title).order_by(CatalogProduct.id).limit(3)))
    source = await read_source(_legacy_db(tmp_path / "old.db", titles),
                               {"users": "users", "subscriptions": "subscriptions", "payments": "payments"})

    async def counts():
        async with sessionmaker()() as s:
            return [await s.scalar(select(func.count()).select_from(m)) for m in (User, Subscription, Entitlement)]

    before = await counts()
    async with sessionmaker()() as s:
        dry = await run_import(s, source, apply=False)
    assert await counts() == before, "quruq yurish hech narsa yozmasligi kerak"

    async with sessionmaker()() as s:
        report = await run_import(s, source, apply=True)
    assert report.counts() == dry.counts() == {
        "purchase.created": 2, "purchase.review": 2,
        "subscription.created": 1, "subscription.skipped": 1,
        "user.created": 4, "user.exists": 1, "user.skipped": 1,
    }
    assert await counts() == [before[0] + 4, before[1] + 1, before[2] + 2]

    async with sessionmaker()() as s:
        tg = await s.scalar(select(User).where(User.telegram_id == "555"))
        assert tg.phone is None and tg.password_hash is None  # taxmin qilinadigan eski parol ko'chmaydi
        old_admin = await s.scalar(select(User).where(User.phone == "+998901110001"))
        assert old_admin.role == "user"
        aziz2 = await s.scalar(select(User).where(User.phone == "+998901112211"))  # 9 xonali raqam normallashdi
        assert aziz2 is not None

    again = await run_import(sessionmaker()(), source, apply=True)
    assert await counts() == [before[0] + 4, before[1] + 1, before[2] + 2], "qayta ishga tushirish dublikat qilmasin"
    assert again.counts()["user.exists"] == 5 and again.counts()["purchase.exists"] == 2

    # Eski parol bilan kirish ishlaydi va xesh yangi formatga o'tadi
    r = await client.post("/v1/auth/login", json={"phone": "+998901112200", "password": "eski-parol-123"})
    assert r.status_code == 200
    async with sessionmaker()() as s:
        assert (await s.scalar(select(User.password_hash).where(User.phone == "+998901112200"))).startswith("scrypt$")
    assert (await client.post("/v1/auth/login", json={"phone": "+998901112200", "password": "eski-parol-123"})).status_code == 200


async def test_read_source_reports_missing_columns(tmp_path):
    from app.legacy_import import read_source

    path = tmp_path / "bad.db"
    c = sqlite3.connect(path)
    c.executescript("CREATE TABLE users (id TEXT, telefon TEXT); CREATE TABLE subscriptions (id INT); CREATE TABLE payments (id INT);")
    c.close()
    with pytest.raises(SystemExit, match="phone"):
        await read_source(f"sqlite+aiosqlite:///{path}", {"users": "users", "subscriptions": "subscriptions", "payments": "payments"})


@pytest.mark.parametrize(("url", "expected"), [
    ("postgres://u:p@h/db", "postgresql+asyncpg://u:p@h/db"),
    ("postgresql://u:p@h:5432/db", "postgresql+asyncpg://u:p@h:5432/db"),
    ("postgresql+psycopg2://u:p@h/db", "postgresql+asyncpg://u:p@h/db"),
    ("postgres://u:p@dpg-x.frankfurt-postgres.render.com/db?sslmode=require",
     "postgresql+asyncpg://u:p@dpg-x.frankfurt-postgres.render.com/db?ssl=require"),
    ("sqlite:////data/uzbizness.db", "sqlite+aiosqlite:////data/uzbizness.db"),
    ("sqlite+aiosqlite:///x.db", "sqlite+aiosqlite:///x.db"),
])
def test_async_url_accepts_old_site_formats(url, expected):
    from app.legacy_import import async_url

    assert async_url(url) == expected


def test_async_url_rejects_unknown():
    from app.legacy_import import async_url

    for bad in ("mysql://x/y", "not-a-url"):
        with pytest.raises(SystemExit):
            async_url(bad)



def test_pasted_url_is_cleaned_and_bad_host_explained():
    import pytest

    from app.legacy_import import async_url, check_host, clean_source_url

    pasted = "\x1b[200~postgresql://u:p@dpg-abc.oregon-postgres.render.com/db?sslmode=require\x1b[201~\n"
    assert clean_source_url(pasted) == "postgresql://u:p@dpg-abc.oregon-postgres.render.com/db?sslmode=require"
    assert async_url(pasted) == "postgresql+asyncpg://u:p@dpg-abc.oregon-postgres.render.com/db?ssl=require"
    check_host(async_url(pasted))
    with pytest.raises(SystemExit) as e:
        check_host("postgresql+asyncpg://u:p@host..com/db")
    assert "xost noto'g'ri" in str(e.value) and ":p@" not in str(e.value)
    with pytest.raises(SystemExit) as e:
        async_url("read -rs")
    assert "read -rs" in str(e.value)  # faqat boshi ko'rsatiladi


def _live_schema_db(path, product_ids: list[str], titles: list[str]) -> str:
    """Jonli eski bazaning haqiqiy `payments` tuzilishi (2026-11-11 staging'da ko'rilgan ustunlar)."""
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE users (id TEXT PRIMARY KEY, phone TEXT, first_name TEXT);
        CREATE TABLE subscriptions (id INTEGER PRIMARY KEY, user_id TEXT, plan_name TEXT, status TEXT, end_date DATETIME);
        CREATE TABLE payments (id TEXT PRIMARY KEY, order_id TEXT, user_id TEXT, user_name TEXT, project_name TEXT,
            product_id TEXT, amount NUMERIC, payment_provider TEXT, payment_status TEXT, admin_status TEXT,
            receipt_file TEXT, created_at DATETIME);
    """)
    c.executemany("INSERT INTO users VALUES (?,?,?)", [
        ("u1", "+998901112200", "Aziz"), ("u2", "+998901112201", "Aziz"), ("u3", "+998901112202", "Vali")])
    c.executemany("INSERT INTO payments VALUES (?,?,?,?,?,?,?,?,?,?,NULL,'2025-03-01')", [
        ("p1", "o1", "u2", "Aziz", titles[0], product_ids[0], 25000, "click", "success", "pending"),   # user_id: aniq
        ("p2", "o2", None, "Vali", titles[1], product_ids[1], 25000, "card", "pending", "approved"),   # karta, tasdiqlangan
        ("p3", "o3", "u1", "Aziz", titles[2], product_ids[2], 25000, "payme", "pending", "pending"),   # to'lanmagan
        ("p4", "o4", "u1", "Aziz", "Standart obuna", None, 50000, "click", "success", "pending"),     # obuna: emas
        ("p5", "o5", "u1", "Aziz", titles[2], None, 25000, "click", "success", "pending"),            # id yo'q: review
        ("p6", "o6", "u1", "Aziz", "Yo'q reja", "yoq-id", 25000, "click", "success", "pending"),       # topilmadi
        ("p7", "o7", None, "Aziz", titles[0], product_ids[0], 25000, "click", "success", "pending"),  # 2 ta Aziz
        ("p8", "o8", "u1", "Aziz", "Mening loyiham", None, 50000, "card", "success", "approved"),     # bitta reja
    ])
    c.commit()
    c.close()
    return f"sqlite+aiosqlite:///{path}"


async def test_import_live_payments_schema(client, tmp_path):
    from app.db.session import sessionmaker
    from app.legacy_import import read_source, run_import
    from app.models import CatalogProduct

    async with sessionmaker()() as s:
        rows = (await s.execute(select(CatalogProduct.id, CatalogProduct.title).order_by(CatalogProduct.id).limit(3))).all()
    ids, titles = [r[0] for r in rows], [r[1] for r in rows]
    source = await read_source(_live_schema_db(tmp_path / "live.db", ids, titles),
                               {"users": "users", "subscriptions": "subscriptions", "payments": "payments"})
    async with sessionmaker()() as s:
        report = await run_import(s, source, apply=False)
    c = report.counts()
    assert c["purchase.created"] == 2  # p1 (user_id), p2 (karta tasdiqlangan, yagona Vali)
    assert c["purchase.review"] == 3   # p5 (id yo'q), p6 (topilmadi), p7 (2 ta Aziz)
    assert c["user.created"] == 3
