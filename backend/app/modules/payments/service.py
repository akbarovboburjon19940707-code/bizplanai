"""To'lov yaratish, tasdiqlash va bekor qilish. Huquq berish faqat shu yerda, bitta tranzaksiyada."""
import base64
import logging
import secrets
from datetime import timedelta
from urllib.parse import urlencode

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError, not_found
from app.core.security import utcnow
from app.models import (AuditLog, CatalogProduct, Entitlement, Payment, PaymentEvent, Subscription, Tariff, User)
from app.storage import get_storage

log = logging.getLogger(__name__)
PREFIX = {"subscription": "sub", "catalog": "cat", "plan_credit": "crd"}


def enabled_providers() -> dict[str, bool]:
    s = get_settings()
    return {
        "click": bool(s.click_service_id and s.click_merchant_id and s.click_secret_key),
        "payme": bool(s.payme_merchant_id and s.payme_secret_key),
        "manual": bool(s.manual_card_number),
    }


async def _price_and_title(session: AsyncSession, user: User, kind: str, target_id: str | None) -> tuple[int, str, str | None]:
    if kind == "subscription":
        tariff = await session.get(Tariff, target_id or "")
        if not tariff or not tariff.is_active or tariff.price_tiyin <= 0:
            raise not_found("Tarif topilmadi")
        return tariff.price_tiyin, f"{tariff.name} obuna ({tariff.duration_days} kun)", tariff.code
    if kind == "catalog":
        product = await session.get(CatalogProduct, target_id or "")
        if not product or not product.is_active:
            raise not_found("Mahsulot topilmadi")
        owned = await session.scalar(select(Entitlement.id).where(
            Entitlement.user_id == user.id, Entitlement.product_id == product.id, Entitlement.revoked_at.is_(None)))
        if owned:
            raise AppError(409, "already_owned", "Bu reja allaqachon sotib olingan")
        # Fayli yo'q rejaga pul olinmasin (aks holda mijoz to'lab, yuklab ololmaydi)
        if not await get_storage().exists(product.file_key):
            log.error("katalog fayli yo'q, sotuv to'xtatildi: product=%s key=%s", product.id, product.file_key)
            raise AppError(409, "file_missing", "Bu reja fayli hozircha mavjud emas. Administrator xabardor qilindi.")
        return product.price_tiyin, product.title, product.id
    if kind == "plan_credit":
        return get_settings().plan_credit_price_som * 100, "Bitta biznes-reja (AI bilan)", None
    raise AppError(400, "bad_kind", "Noma'lum to'lov turi")


async def create_payment(session: AsyncSession, user: User, kind: str, target_id: str | None, provider: str) -> Payment:
    if not enabled_providers().get(provider):
        raise AppError(400, "provider_unavailable", "Bu to'lov usuli hozircha mavjud emas")
    amount, title, target = await _price_and_title(session, user, kind, target_id)
    payment = Payment(id=f"{PREFIX[kind]}_{secrets.token_hex(8)}", user_id=user.id, kind=kind, target_id=target,
                      title=title, amount_tiyin=amount, provider=provider, status="pending", updated_at=utcnow())
    session.add(payment)
    session.add(PaymentEvent(payment_id=payment.id, source="api", event="created", data={"provider": provider}))
    await session.commit()
    return payment


def checkout(payment: Payment) -> dict:
    s = get_settings()
    return_url = f"{s.frontend_url.rstrip('/')}/tolov/{payment.id}"
    if payment.provider == "click":
        q = urlencode({"service_id": s.click_service_id, "merchant_id": s.click_merchant_id,
                       "amount": f"{payment.amount_tiyin / 100:.2f}", "transaction_param": payment.id,
                       "return_url": return_url})
        return {"type": "redirect", "url": f"https://my.click.uz/services/pay?{q}"}
    if payment.provider == "payme":
        raw = f"m={s.payme_merchant_id};ac.order_id={payment.id};ac.product_id=1;a={payment.amount_tiyin};c={return_url};l=uz"
        return {"type": "redirect", "url": f"{s.payme_checkout_url}/{base64.b64encode(raw.encode()).decode()}"}
    return {"type": "manual", "card_number": s.manual_card_number, "card_holder": s.manual_card_holder,
            "amount_som": payment.amount_tiyin // 100,
            "instructions": "Summani kartaga o'tkazing va chek rasmini yuklang. Administrator tekshirgach faollashadi."}


async def lock_payment(session: AsyncSession, payment_id: str) -> Payment | None:
    stmt = select(Payment).where(Payment.id == payment_id)
    if session.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update()
    return await session.scalar(stmt)


async def _grant(session: AsyncSession, p: Payment) -> None:
    if p.kind == "subscription":
        tariff = await session.get(Tariff, p.target_id)
        now = utcnow()
        latest = await session.scalar(select(Subscription.ends_at).where(
            Subscription.user_id == p.user_id, Subscription.status == "active", Subscription.ends_at > now)
            .order_by(Subscription.ends_at.desc()).limit(1))
        start = max(now, latest) if latest else now  # muddat ustiga qo'shiladi
        session.add(Subscription(user_id=p.user_id, tariff_code=tariff.code, starts_at=start,
                                 ends_at=start + timedelta(days=tariff.duration_days), payment_id=p.id))
    elif p.kind == "catalog":
        session.add(Entitlement(user_id=p.user_id, product_id=p.target_id, payment_id=p.id))
    elif p.kind == "plan_credit":
        await session.execute(update(User).where(User.id == p.user_id).values(plan_credits=User.plan_credits + 1))


async def _ungrant(session: AsyncSession, p: Payment) -> None:
    now = utcnow()
    if p.kind == "subscription":
        await session.execute(update(Subscription).where(Subscription.payment_id == p.id).values(status="revoked"))
    elif p.kind == "catalog":
        await session.execute(update(Entitlement).where(Entitlement.payment_id == p.id, Entitlement.revoked_at.is_(None))
                              .values(revoked_at=now))
    elif p.kind == "plan_credit":
        await session.execute(update(User).where(User.id == p.user_id, User.plan_credits > 0)
                              .values(plan_credits=User.plan_credits - 1))


async def mark_paid(session: AsyncSession, p: Payment, source: str, actor_id: str | None = None,
                    note: str | None = None, data: dict | None = None) -> bool:
    """Idempotent: qayta chaqirilsa huquq ikkinchi marta berilmaydi."""
    if p.status == "paid":
        return False
    p.status, p.paid_at, p.updated_at = "paid", utcnow(), utcnow()
    if note:
        p.admin_note = note[:500]
    await _grant(session, p)
    session.add(PaymentEvent(payment_id=p.id, source=source, event="paid", data=data))
    session.add(AuditLog(actor_id=actor_id, action="payment.paid", entity="payment", entity_id=p.id,
                         data={"source": source, "amount_tiyin": p.amount_tiyin}))
    return True


async def mark_cancelled(session: AsyncSession, p: Payment, source: str, new_status: str = "cancelled",
                         actor_id: str | None = None, note: str | None = None, data: dict | None = None) -> None:
    if p.status in ("cancelled", "rejected"):
        return
    if p.status == "paid":
        await _ungrant(session, p)
    p.status, p.updated_at = new_status, utcnow()
    if note:
        p.admin_note = note[:500]
    session.add(PaymentEvent(payment_id=p.id, source=source, event=new_status, data=data))
    session.add(AuditLog(actor_id=actor_id, action=f"payment.{new_status}", entity="payment", entity_id=p.id,
                         data={"source": source}))
