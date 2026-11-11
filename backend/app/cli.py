"""Boshqaruv buyruqlari:
  python -m app.cli seed [--min-catalog-price 25000]
  python -m app.cli create-admin --phone +998901234567 --password '...'
  python -m app.cli import-legacy --source postgresql://... [--apply] [--report hisobot.csv]
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

        def category_key(label: str | None) -> str:
            # "Transport / Lizing" kabi kengaytirilgan nomlar asosiy kategoriyaga ("Transport") tushadi
            raw = (label or "").strip()
            key = label_to_key.get(raw) or label_to_key.get(raw.split("/")[0].strip())
            if not key:
                raise ValueError(f"catalog.json: noma'lum kategoriya {raw!r}")
            return key
        added = 0
        for p in catalog.get("all_products", []):
            if await s.get(CatalogProduct, str(p["id"])) is not None:
                continue
            price = max(int(p.get("price") or 0), min_price_som)
            s.add(CatalogProduct(
                id=str(p["id"]), slug=p.get("slug") or str(p["id"]),
                category_key=category_key(p.get("category")),
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


async def import_legacy(source_url: str, apply: bool, report_path: str | None, tables: dict[str, str]) -> None:
    from app.legacy_import import read_source, run_import

    source = await read_source(source_url, tables)
    print(f"eski baza: {len(source['users'])} foydalanuvchi, {len(source['subscriptions'])} obuna, "
          f"{len(source['payments'])} to'lov")
    async with sessionmaker()() as s:
        report = await run_import(s, source, apply=apply)
    await dispose_engine()
    for key, n in report.counts().items():
        print(f"  {key}: {n}")
    if report_path:
        report.write_csv(report_path)
        print(f"hisobot: {report_path}")
    print("YOZILDI" if apply else "QURUQ YURISH: hech narsa yozilmadi (--apply bilan yozing)")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_seed = sub.add_parser("seed")
    p_seed.add_argument("--min-catalog-price", type=int, default=25000)
    p_admin = sub.add_parser("create-admin")
    p_admin.add_argument("--phone", required=True)
    p_admin.add_argument("--password", required=True)
    p_legacy = sub.add_parser("import-legacy")
    p_legacy.add_argument("--source", required=True, help="eski saytning DATABASE_URL i")
    p_legacy.add_argument("--apply", action="store_true", help="yozish (bo'lmasa faqat hisobot)")
    p_legacy.add_argument("--report", help="CSV hisobot fayli")
    p_legacy.add_argument("--users-table", default="users")
    p_legacy.add_argument("--subscriptions-table", default="subscriptions")
    p_legacy.add_argument("--payments-table", default="payments")
    args = parser.parse_args()
    if args.cmd == "seed":
        asyncio.run(seed(args.min_catalog_price))
    elif args.cmd == "import-legacy":
        tables = {"users": args.users_table, "subscriptions": args.subscriptions_table, "payments": args.payments_table}
        asyncio.run(import_legacy(args.source, args.apply, args.report, tables))
    else:
        if len(args.password) < 12:
            raise SystemExit("Admin paroli kamida 12 belgi bo'lsin")
        asyncio.run(create_admin(args.phone, args.password))


if __name__ == "__main__":
    main()
