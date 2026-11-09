"""Boshqaruv buyruqlari:
  python -m app.cli seed [--min-catalog-price 25000]
  python -m app.cli create-admin --phone +998901234567 --password '...'
"""
import argparse
import asyncio
import json
import os

from sqlalchemy import select

from app.core.security import hash_password, new_totp_secret, totp_uri
from app.db.session import dispose_engine, sessionmaker
from app.models import CatalogCategory, CatalogProduct, Tariff, User
from app.modules.auth.schemas import normalize_phone

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

# Hozirgi saytdagi narx va limitlar (PLAN_META). Biznes qarori bilan o'zgartiriladi.
TARIFFS = [
    dict(code="basic", name="Bepul", price_tiyin=0, duration_days=0, daily_limit=3, monthly_limit=10, ai_enabled=False, sort=0),
    dict(code="pro", name="Standart", price_tiyin=50_000_00, duration_days=30, daily_limit=15, monthly_limit=50, ai_enabled=True, sort=1),
    dict(code="enterprise", name="Premium", price_tiyin=500_000_00, duration_days=30, daily_limit=50, monthly_limit=500, ai_enabled=True, sort=2),
]


async def seed(min_price_som: int) -> None:
    async with sessionmaker()() as s:
        for t in TARIFFS:
            existing = await s.get(Tariff, t["code"])
            if existing is None:
                s.add(Tariff(**t))
        with open(os.path.join(DATA, "catalog.json"), encoding="utf-8") as f:
            catalog = json.load(f)
        for i, c in enumerate(catalog.get("categories", [])):
            if await s.get(CatalogCategory, c["key"]) is None:
                s.add(CatalogCategory(key=c["key"], label=c["label"], icon=c.get("icon", ""), sort=i))
        await s.flush()
        label_to_key = {c["label"]: c["key"] for c in catalog.get("categories", [])}
        added = 0
        for p in catalog.get("all_products", []):
            if await s.get(CatalogProduct, str(p["id"])) is not None:
                continue
            price = max(int(p.get("price") or 0), min_price_som)
            s.add(CatalogProduct(
                id=str(p["id"]), slug=p.get("slug") or str(p["id"]),
                category_key=label_to_key.get(p.get("category"), catalog["categories"][0]["key"]),
                title=p["title"], description=p.get("description", ""), price_tiyin=price * 100,
                file_key=f"catalog/pdfs/{p['id']}{p.get('file_extension') or '.pdf'}",
                file_size=p.get("file_size_formatted", ""), preview_image=p.get("preview_image", ""),
                views=int(p.get("views_count") or 0), downloads=int(p.get("download_count") or 0)))
            added += 1
        await s.commit()
        print(f"tariflar: {len(TARIFFS)}, katalogga qo'shildi: {added}")
    await dispose_engine()


async def create_admin(phone: str, password: str) -> None:
    phone = normalize_phone(phone)
    secret = new_totp_secret()
    async with sessionmaker()() as s:
        user = await s.scalar(select(User).where(User.phone == phone))
        if user is None:
            user = User(phone=phone, first_name="Admin")
            s.add(user)
        user.password_hash, user.role, user.totp_secret = hash_password(password), "admin", secret
        await s.commit()
    await dispose_engine()
    print("Admin tayyor. Google Authenticator yoki shunga o'xshash ilovaga qo'shing:")
    print(totp_uri(secret, phone))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_seed = sub.add_parser("seed")
    p_seed.add_argument("--min-catalog-price", type=int, default=25000)
    p_admin = sub.add_parser("create-admin")
    p_admin.add_argument("--phone", required=True)
    p_admin.add_argument("--password", required=True)
    args = parser.parse_args()
    if args.cmd == "seed":
        asyncio.run(seed(args.min_catalog_price))
    else:
        if len(args.password) < 12:
            raise SystemExit("Admin paroli kamida 12 belgi bo'lsin")
        asyncio.run(create_admin(args.phone, args.password))


if __name__ == "__main__":
    main()
