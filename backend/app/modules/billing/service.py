"""Tarif, obuna va atomik kvota.

Biznes qoidasi (tariflar jadvalidan sozlanadi):
1. Faol obuna bo'lsa: obuna tarifining kunlik/oylik limiti, AI tarifga bog'liq.
2. Obuna limiti tugasa yoki obuna bo'lmasa: bir martalik kredit (plan_credits) bo'lsa, u sarflanadi va AI beriladi.
3. Kredit ham bo'lmasa: bepul 'basic' tarif limiti (AI yo'q).
4. Hammasi tugasa: 429 quota_exceeded.
"""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import utcnow
from app.models import Subscription, Tariff, UsageCounter, User

FREE_TARIFF = "basic"


@dataclass
class QuotaGrant:
    source: str  # subscription | credit | free
    ai_allowed: bool
    period_keys: tuple[str, ...]


def period_keys(now: datetime | None = None) -> tuple[str, str]:
    now = now or utcnow()
    return f"d:{now:%Y-%m-%d}", f"m:{now:%Y-%m}"


async def active_subscription(session: AsyncSession, user_id: str) -> Subscription | None:
    now = utcnow()
    return await session.scalar(
        select(Subscription).where(Subscription.user_id == user_id, Subscription.status == "active",
                                   Subscription.starts_at <= now, Subscription.ends_at > now)
        .order_by(Subscription.ends_at.desc()).limit(1)
    )


async def usage(session: AsyncSession, user_id: str) -> dict[str, int]:
    day, month = period_keys()
    rows = await session.execute(select(UsageCounter.period_key, UsageCounter.used)
                                 .where(UsageCounter.user_id == user_id, UsageCounter.period_key.in_([day, month])))
    found = dict(rows.all())
    return {"daily_used": found.get(day, 0), "monthly_used": found.get(month, 0)}


async def _ensure_rows(session: AsyncSession, user_id: str, keys: tuple[str, ...]) -> None:
    ins = pg_insert if session.bind.dialect.name == "postgresql" else sqlite_insert
    stmt = ins(UsageCounter).values([{"user_id": user_id, "period_key": k, "used": 0} for k in keys])
    await session.execute(stmt.on_conflict_do_nothing())


async def _try_counters(session: AsyncSession, user_id: str, tariff: Tariff) -> tuple[str, ...] | None:
    """Kunlik va oylik hisoblagichni shart bilan oshiradi. Ikkalasi ham sig'sa kalitlarni qaytaradi."""
    day, month = period_keys()
    await _ensure_rows(session, user_id, (day, month))
    done: list[str] = []
    for key, limit in ((day, tariff.daily_limit), (month, tariff.monthly_limit)):
        res = await session.execute(
            update(UsageCounter).where(UsageCounter.user_id == user_id, UsageCounter.period_key == key,
                                       UsageCounter.used < limit).values(used=UsageCounter.used + 1)
        )
        if res.rowcount != 1:
            for k in done:  # yarim bajarilganini qaytarish
                await session.execute(update(UsageCounter).where(UsageCounter.user_id == user_id,
                                                                 UsageCounter.period_key == k)
                                      .values(used=UsageCounter.used - 1))
            return None
        done.append(key)
    return tuple(done)


async def consume_quota(session: AsyncSession, user: User) -> QuotaGrant:
    sub = await active_subscription(session, user.id)
    if sub:
        tariff = await session.get(Tariff, sub.tariff_code)
        if tariff:
            keys = await _try_counters(session, user.id, tariff)
            if keys:
                return QuotaGrant("subscription", tariff.ai_enabled, keys)

    res = await session.execute(update(User).where(User.id == user.id, User.plan_credits > 0)
                                .values(plan_credits=User.plan_credits - 1))
    if res.rowcount == 1:
        return QuotaGrant("credit", True, ())

    if not sub:
        free = await session.get(Tariff, FREE_TARIFF)
        if free:
            keys = await _try_counters(session, user.id, free)
            if keys:
                return QuotaGrant("free", free.ai_enabled, keys)

    raise AppError(429, "quota_exceeded", "Limit tugadi. Tarifni yangilang yoki bitta reja sotib oling.",
                   {"upgrade_url": "/tariflar"})


async def refund_quota(session: AsyncSession, user_id: str, source: str, keys: tuple[str, ...]) -> None:
    if source == "credit":
        await session.execute(update(User).where(User.id == user_id).values(plan_credits=User.plan_credits + 1))
    for k in keys:
        await session.execute(update(UsageCounter).where(UsageCounter.user_id == user_id, UsageCounter.period_key == k,
                                                         UsageCounter.used > 0).values(used=UsageCounter.used - 1))
