"""Boshqaruv buyruqlari:
  python -m app.cli seed [--min-catalog-price 25000]
  python -m app.cli create-admin --phone +998901234567 --password '...'
  python -m app.cli check-catalog [--hide-missing] [--report katalog.csv]
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


async def check_catalog(hide_missing: bool, report_path: str | None) -> None:
    """Faol katalog rejalarining PDF va muqova rasmi saqlashda (R2) borligini tekshiradi."""
    import csv

    from app.models import AuditLog
    from app.modules.catalog.router import image_key
    from app.storage import get_storage

    storage = get_storage()
    limit = asyncio.Semaphore(16)

    async def probe(p: CatalogProduct) -> dict:
        async with limit:
            img = image_key(p.preview_image)
            return {"id": p.id, "title": p.title, "pdf": await storage.exists(p.file_key),
                    "image": (await storage.exists(img)) if img else None, "file_key": p.file_key}

    async with sessionmaker()() as s:
        products = list(await s.scalars(select(CatalogProduct).where(CatalogProduct.is_active.is_(True))))
        rows = await asyncio.gather(*(probe(p) for p in products))
        no_pdf = [r for r in rows if not r["pdf"]]
        no_img = [r for r in rows if r["image"] is False]
        print(f"faol rejalar: {len(rows)}, PDF yo'q: {len(no_pdf)}, rasm yo'q: {len(no_img)}, "
              f"rasm ko'rsatilmagan: {sum(r['image'] is None for r in rows)}")
        for r in no_pdf[:20]:
            print(f"  PDF yo'q: {r['id']}  ({r['file_key']})")
        if hide_missing and no_pdf:
            ids = {r["id"] for r in no_pdf}
            for p in products:
                if p.id in ids:
                    p.is_active = False
                    s.add(AuditLog(actor_id=None, action="catalog.hide_missing_file", entity="product", entity_id=p.id))
            await s.commit()
            print(f"{len(ids)} ta reja yashirildi (admin panel > Katalog > Yashirilgan; fayl yuklangach Ko'rsatish)")
    await dispose_engine()
    if report_path:
        with open(report_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["id", "title", "pdf", "image", "file_key"])
            w.writeheader()
            w.writerows(rows)
        print(f"hisobot: {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_seed = sub.add_parser("seed")
    p_seed.add_argument("--min-catalog-price", type=int, default=25000)
    p_admin = sub.add_parser("create-admin")
    p_admin.add_argument("--phone", required=True)
    p_admin.add_argument("--password", required=True)
    p_check = sub.add_parser("check-catalog")
    p_check.add_argument("--hide-missing", action="store_true", help="PDF fayli yo'q rejalarni katalogdan yashirish")
    p_check.add_argument("--report", help="CSV hisobot fayli")
    args = parser.parse_args()
    if args.cmd == "seed":
        asyncio.run(seed(args.min_catalog_price))
    elif args.cmd == "check-catalog":
        asyncio.run(check_catalog(args.hide_missing, args.report))
    else:
        if len(args.password) < 12:
            raise SystemExit("Admin paroli kamida 12 belgi bo'lsin")
        asyncio.run(create_admin(args.phone, args.password))


if __name__ == "__main__":
    main()
