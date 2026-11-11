"""Admin: foydalanuvchiga tarif (obuna) yoki bir martalik reja (kredit) berish va obunani bekor qilish.

Huquq faqat `payments.service.mark_paid` orqali beriladi (arxitektura qoidasi): har berish 0 so'mlik `provider="admin"`
to'lov sifatida yoziladi. Shunda foydalanuvchi to'lovlar tarixida, admin to'lovlar ro'yxatida va audit jurnalida iz qoladi,
tushum statistikasi esa o'zgarmaydi (summa 0).
"""
import secrets
from datetime import timedelta
from typing import Annotated, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.deps import AdminUser, SessionDep
from app.core.errors import AppError, not_found
from app.core.security import utcnow
from app.models import AuditLog, Payment, PaymentEvent, Subscription, Tariff, User
from app.modules.auth.schemas import UserOut
from app.modules.payments.service import PREFIX, lock_payment, mark_cancelled, mark_paid

router = APIRouter()
MAX_CREDITS = 20


class SubscriptionGrantIn(BaseModel):
    kind: Literal["subscription"]
    tariff_code: str = Field(min_length=1, max_length=32)
    days: int | None = Field(default=None, ge=1, le=366)  # berilmasa tarif muddati (30 kun)
    note: str = Field(default="", max_length=300)


class CreditsGrantIn(BaseModel):
    kind: Literal["credits"]
    count: int = Field(ge=1, le=MAX_CREDITS)
    note: str = Field(default="", max_length=300)


GrantIn = Annotated[SubscriptionGrantIn | CreditsGrantIn, Field(discriminator="kind")]


class AdminSubscriptionOut(BaseModel):
    id: str
    tariff_code: str
    tariff_name: str
    starts_at: str
    ends_at: str
    status: str  # active | revoked | expired
    source: str  # admin | payment | legacy


class AdminGrantOut(BaseModel):
    id: str
    kind: str
    title: str
    status: str
    note: str
    created_at: str


class TariffChoice(BaseModel):
    code: str
    name: str
    duration_days: int


class UserBillingOut(BaseModel):
    user: UserOut
    subscriptions: list[AdminSubscriptionOut]
    grants: list[AdminGrantOut]
    tariffs: list[TariffChoice]  # berish mumkin bo'lgan pullik tariflar


def _iso(dt) -> str:
    return dt.isoformat() + "Z"


async def _billing(session, user: User) -> UserBillingOut:
    now = utcnow()
    tariffs = {t.code: t for t in await session.scalars(select(Tariff))}
    subs = list(await session.scalars(select(Subscription).where(Subscription.user_id == user.id)
                                      .order_by(Subscription.ends_at.desc()).limit(20)))
    pay_ids = [s.payment_id for s in subs if s.payment_id and not s.payment_id.startswith("lg")]
    providers = dict((await session.execute(select(Payment.id, Payment.provider).where(Payment.id.in_(pay_ids)))).all()) \
        if pay_ids else {}

    def source(s: Subscription) -> str:
        if s.payment_id and s.payment_id.startswith("lg"):
            return "legacy"
        return "admin" if providers.get(s.payment_id or "") == "admin" else "payment"

    grants = list(await session.scalars(select(Payment).where(Payment.user_id == user.id, Payment.provider == "admin")
                                        .order_by(Payment.created_at.desc()).limit(30)))
    return UserBillingOut(
        user=UserOut.model_validate(user),
        subscriptions=[AdminSubscriptionOut(
            id=s.id, tariff_code=s.tariff_code, tariff_name=tariffs[s.tariff_code].name if s.tariff_code in tariffs else s.tariff_code,
            starts_at=_iso(s.starts_at), ends_at=_iso(s.ends_at), source=source(s),
            status="revoked" if s.status != "active" else ("expired" if s.ends_at <= now else "active")) for s in subs],
        grants=[AdminGrantOut(id=g.id, kind=g.kind, title=g.title, status=g.status, note=g.admin_note or "",
                              created_at=_iso(g.created_at)) for g in grants],
        tariffs=[TariffChoice(code=t.code, name=t.name, duration_days=t.duration_days)
                 for t in sorted(tariffs.values(), key=lambda t: t.sort) if t.is_active and t.price_tiyin > 0],
    )


async def _user(session, user_id: str) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise not_found("Foydalanuvchi topilmadi")
    return user


@router.get("/users/{user_id}/billing", response_model=UserBillingOut)
async def user_billing(user_id: str, _: AdminUser, session: SessionDep):
    return await _billing(session, await _user(session, user_id))


async def _admin_payment(session, user: User, kind: str, target_id: str | None, title: str) -> Payment:
    p = Payment(id=f"{PREFIX[kind]}_{secrets.token_hex(8)}", user_id=user.id, kind=kind, target_id=target_id,
                title=title, amount_tiyin=0, provider="admin", status="pending", updated_at=utcnow())
    session.add(p)
    session.add(PaymentEvent(payment_id=p.id, source="admin", event="created", data={"grant": True}))
    await session.flush()
    return p


@router.post("/users/{user_id}/grant", response_model=UserBillingOut)
async def grant(user_id: str, data: GrantIn, admin: AdminUser, session: SessionDep):
    user = await _user(session, user_id)
    note = data.note.strip() or "Admin tomonidan berildi"
    if isinstance(data, SubscriptionGrantIn):
        tariff = await session.get(Tariff, data.tariff_code)
        if not tariff or not tariff.is_active or tariff.price_tiyin <= 0:
            raise AppError(400, "bad_tariff", "Bunday pullik tarif yo'q")
        days = data.days or tariff.duration_days
        p = await _admin_payment(session, user, "subscription", tariff.code, f"{tariff.name} obuna ({days} kun, admin)")
        await mark_paid(session, p, "admin", actor_id=admin.id, note=note, data={"days": days})
        await session.flush()
        if days != tariff.duration_days:  # _grant tarif muddatini qo'yadi; admin boshqa muddat tanlagan bo'lsa tuzatamiz
            sub = await session.scalar(select(Subscription).where(Subscription.payment_id == p.id))
            sub.ends_at = sub.starts_at + timedelta(days=days)
        action, payload = "grant.subscription", {"tariff": tariff.code, "days": days, "payment_id": p.id}
    else:
        ids = []
        for _ in range(data.count):  # har kredit alohida 0 so'mlik to'lov: bekor qilish va iz aniq bo'ladi
            p = await _admin_payment(session, user, "plan_credit", None, "Bitta biznes-reja (admin)")
            await mark_paid(session, p, "admin", actor_id=admin.id, note=note)
            ids.append(p.id)
        action, payload = "grant.credits", {"count": data.count, "payment_ids": ids}
    session.add(AuditLog(actor_id=admin.id, action=action, entity="user", entity_id=user.id, data={**payload, "note": note}))
    await session.commit()
    await session.refresh(user)
    return await _billing(session, user)


class RevokeIn(BaseModel):
    note: str = Field(default="", max_length=300)


@router.post("/subscriptions/{subscription_id}/revoke", response_model=UserBillingOut)
async def revoke_subscription(subscription_id: str, data: RevokeIn, admin: AdminUser, session: SessionDep):
    sub = await session.get(Subscription, subscription_id)
    if not sub:
        raise not_found("Obuna topilmadi")
    if sub.status != "active":
        raise AppError(409, "already_revoked", "Obuna allaqachon bekor qilingan")
    note = data.note.strip() or "Admin bekor qildi"
    payment = await lock_payment(session, sub.payment_id) if sub.payment_id else None
    if payment and payment.provider == "admin":
        await mark_cancelled(session, payment, "admin", actor_id=admin.id, note=note)  # obuna ham revoked bo'ladi
    else:
        # Haqiqiy to'lov yoki eski saytdan ko'chgan obuna: to'lov yozuvi o'zgarmaydi (pul qaytarish alohida), faqat obuna
        sub.status = "revoked"
    session.add(AuditLog(actor_id=admin.id, action="subscription.revoke", entity="subscription", entity_id=sub.id,
                         data={"user_id": sub.user_id, "payment_id": sub.payment_id, "note": note}))
    await session.commit()
    return await _billing(session, await _user(session, sub.user_id))
