"""Eski sayt (reference/old-uzbiznesss, Flask) bazasidan foydalanuvchi, faol obuna va katalog xaridlarini ko'chirish.

python -m app.cli import-legacy --source postgresql://... [--apply] [--report hisobot.csv]

- Standart: quruq yurish (hamma narsa hisoblanadi, tranzaksiya oxirida bekor qilinadi). `--apply` bilan yoziladi.
- Qayta ishga tushirish xavfsiz: mavjud foydalanuvchi (telefon/telegram_id) qayta yaratilmaydi,
  obuna va huquqlar `lgs:<eski id>` / `lgp:<eski id>` belgisi bilan bir marta yoziladi (ustun 40 belgi).
- Shubhali holatlar (noto'g'ri telefon, bir xil ism bilan bog'langan xarid, topilmagan reja) ko'chirilmaydi,
  hisobotga yoziladi: admin qo'lda hal qiladi.
- Eski Telegram foydalanuvchilari (telefon "tg_<id>") telefonsiz va parolsiz ko'chadi: eski avtomatik
  parollar taxmin qilinadigan edi. Ular Telegram orqali kiradi va kabinetda parol o'rnatishi mumkin.
- Parol xeshlari (Werkzeug) o'zgarishsiz ko'chadi: kirishda tekshiriladi va yangi formatga o'tkaziladi.
"""
import csv
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import MetaData, Table, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.models import CatalogProduct, Entitlement, Subscription, User
from app.modules.auth.schemas import normalize_phone

REQUIRED = {
    "users": {"id", "phone", "first_name"},
    "subscriptions": {"id", "user_id", "plan_name", "status", "end_date"},
    "payments": {"id", "user_name", "payment_status", "payment_type", "loyiha_nomi"},
}
PAID_TARIFFS = {"pro", "enterprise"}


@dataclass
class Report:
    rows: list[dict] = field(default_factory=list)

    def add(self, kind: str, legacy_id: object, action: str, detail: str = "") -> None:
        self.rows.append({"kind": kind, "legacy_id": str(legacy_id), "action": action, "detail": detail})

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.rows:
            key = f"{r['kind']}.{r['action']}"
            out[key] = out.get(key, 0) + 1
        return dict(sorted(out.items()))

    def write_csv(self, path: str) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["kind", "legacy_id", "action", "detail"])
            w.writeheader()
            w.writerows(self.rows)


def _norm(text: object) -> str:
    return " ".join(str(text or "").split()).casefold()


def _naive_utc(value: object) -> datetime | None:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if not isinstance(value, datetime):
        return None
    return value.astimezone(UTC).replace(tzinfo=None) if value.tzinfo else value


def async_url(url: str) -> str:
    """Eski saytdagi URL ko'rinishlari (postgres://, postgresql://, postgresql+psycopg2://, sqlite:///) -> async drayver."""
    scheme, sep, rest = url.partition("://")
    if not sep:
        # manzil parol bo'lishi mumkin: to'liq ko'rsatilmaydi
        raise SystemExit(f"Noto'g'ri baza manzili (boshlanishi: {url[:10]!r}...). "
                         "U postgres:// yoki postgresql:// bilan boshlanishi kerak.")
    base = scheme.split("+", 1)[0]
    if base in ("postgres", "postgresql"):
        # Render'ning tashqi manzili "?sslmode=require" bilan keladi; asyncpg "ssl=" ni tushunadi
        return f"postgresql+asyncpg://{rest.replace('sslmode=', 'ssl=')}"
    if base == "sqlite":
        return f"sqlite+aiosqlite://{rest}"
    raise SystemExit(f"Qo'llab-quvvatlanmaydigan baza: {scheme}")


async def read_source(url: str, tables: dict[str, str]) -> dict[str, list[dict]]:
    """Eski bazani o'qiydi; kerakli ustunlar bo'lmasa aniq xato beradi (eski models/ repo'da yo'q)."""
    engine = create_async_engine(async_url(url))
    try:
        async with engine.connect() as conn:
            meta = MetaData()
            await conn.run_sync(lambda c: meta.reflect(c, only=list(tables.values())))
            data = {}
            for logical, name in tables.items():
                table: Table = meta.tables[name]
                missing = REQUIRED[logical] - set(table.c.keys())
                if missing:
                    raise SystemExit(f"Eski '{name}' jadvalida ustunlar yo'q: {sorted(missing)}. Mavjud: {sorted(table.c.keys())}")
                data[logical] = [dict(r._mapping) for r in await conn.execute(select(table))]
            return data
    finally:
        await engine.dispose()


async def import_users(session: AsyncSession, users: list[dict], report: Report) -> dict[str, str]:
    """Eski user id -> yangi user id."""
    by_phone = {u.phone: u.id for u in await session.scalars(select(User).where(User.phone.is_not(None)))}
    by_tg = {u.telegram_id: u.id for u in await session.scalars(select(User).where(User.telegram_id.is_not(None)))}
    mapping: dict[str, str] = {}
    for old in users:
        raw_phone = str(old.get("phone") or "")
        tg_id = str(old["telegram_id"]) if old.get("telegram_id") else None
        telegram_only = raw_phone.startswith("tg_")
        phone = None
        if not telegram_only:
            try:
                phone = normalize_phone(raw_phone)
            except ValueError:
                if not tg_id:
                    report.add("user", old["id"], "skipped", f"telefon noto'g'ri: {raw_phone!r}")
                    continue
        existing = (phone and by_phone.get(phone)) or (tg_id and by_tg.get(tg_id))
        if existing:
            mapping[str(old["id"])] = existing
            report.add("user", old["id"], "exists", phone or f"tg {tg_id}")
            continue
        user = User(
            phone=phone, first_name=(old.get("first_name") or "")[:100], last_name=(old.get("last_name") or "")[:100],
            email=old.get("email") or None, telegram_id=tg_id, telegram_username=old.get("telegram_username") or None,
            # Telegram-only hisoblarning eski avtomatik paroli taxmin qilinadigan edi: ko'chirilmaydi
            password_hash=None if telegram_only else (old.get("password_hash") or None),
            role="user",  # admin TOTP bilan alohida yaratiladi (python -m app.cli create-admin)
            is_active=bool(old.get("is_active", True)),
        )
        if created := _naive_utc(old.get("created_at")):
            user.created_at = created
        session.add(user)
        await session.flush()
        mapping[str(old["id"])] = user.id
        if phone:
            by_phone[phone] = user.id
        if tg_id:
            by_tg[tg_id] = user.id
        note = "telegram (telefon va parolsiz)" if telegram_only else phone
        if old.get("role") == "admin":
            note += "; eski admin oddiy foydalanuvchi bo'ldi"
        report.add("user", old["id"], "created", note)
    return mapping


async def import_subscriptions(session: AsyncSession, subs: list[dict], users: dict[str, str], report: Report,
                               now: datetime) -> None:
    done = set(await session.scalars(select(Subscription.payment_id).where(Subscription.payment_id.like("lgs:%"))))
    for old in subs:
        ends = _naive_utc(old.get("end_date"))
        if old.get("status") != "active" or not ends or ends <= now or old.get("plan_name") not in PAID_TARIFFS:
            continue  # tugagan yoki bepul: ko'chirish shart emas
        marker = f"lgs:{old['id']}"[:40]
        if marker in done:
            report.add("subscription", old["id"], "exists")
            continue
        user_id = users.get(str(old["user_id"]))
        if not user_id:
            report.add("subscription", old["id"], "skipped", "foydalanuvchi ko'chirilmagan")
            continue
        session.add(Subscription(user_id=user_id, tariff_code=old["plan_name"], status="active", payment_id=marker,
                                 starts_at=_naive_utc(old.get("start_date")) or now, ends_at=ends))
        report.add("subscription", old["id"], "created", f"{old['plan_name']} {ends.date()} gacha")


async def import_purchases(session: AsyncSession, payments: list[dict], old_users: list[dict], users: dict[str, str],
                           report: Report) -> None:
    """Eski katalog xaridlari user_name (ism YOKI telefon) va reja nomi bilan saqlangan: faqat aniq mosini ko'chiramiz."""
    products: dict[str, list[str]] = {}
    for p in await session.scalars(select(CatalogProduct)):
        products.setdefault(_norm(p.title), []).append(p.id)
    by_phone, by_name = {}, {}
    for u in old_users:
        by_phone[str(u.get("phone") or "")] = str(u["id"])
        by_name.setdefault(_norm(u.get("first_name")), []).append(str(u["id"]))
    owned = {(e.user_id, e.product_id) for e in await session.scalars(select(Entitlement))}

    for old in payments:
        if old.get("payment_status") != "success" or old.get("payment_type") != "catalog":
            continue
        name = str(old.get("user_name") or "")
        if name in by_phone:
            old_uid = by_phone[name]
        elif len(by_name.get(_norm(name), [])) == 1:
            old_uid = by_name[_norm(name)][0]
        else:
            matches = len(by_name.get(_norm(name), []))
            report.add("purchase", old["id"], "review", f"egasi aniq emas: user_name={name!r} ({matches} ta mos)")
            continue
        product_ids = products.get(_norm(old.get("loyiha_nomi")), [])
        if len(product_ids) != 1:
            report.add("purchase", old["id"], "review", f"reja topilmadi yoki bir nechta: {old.get('loyiha_nomi')!r}")
            continue
        user_id = users.get(old_uid)
        if not user_id:
            report.add("purchase", old["id"], "skipped", "foydalanuvchi ko'chirilmagan")
            continue
        if (user_id, product_ids[0]) in owned:
            report.add("purchase", old["id"], "exists")
            continue
        session.add(Entitlement(user_id=user_id, product_id=product_ids[0], payment_id=f"lgp:{old['id']}"[:40]))
        owned.add((user_id, product_ids[0]))
        report.add("purchase", old["id"], "created", product_ids[0])


async def run_import(session: AsyncSession, source: dict[str, list[dict]], apply: bool,
                     now: datetime | None = None) -> Report:
    report = Report()
    now = now or datetime.now(UTC).replace(tzinfo=None)
    users = await import_users(session, source["users"], report)
    await import_subscriptions(session, source["subscriptions"], users, report, now)
    await import_purchases(session, source["payments"], source["users"], users, report)
    if apply:
        await session.commit()
    else:
        await session.rollback()
    return report
