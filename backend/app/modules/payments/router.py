import secrets

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import CurrentUser, SessionDep
from app.core.errors import AppError, not_found
from app.core.ratelimit import rate_limit
from app.core.security import utcnow
from app.models import Payment, PaymentEvent
from app.modules.payments import service
from app.modules.payments.schemas import PaymentCreateIn, PaymentCreateOut, PaymentOut, payment_out
from app.modules.telegram.service import notify_admin
from app.storage import get_storage

router = APIRouter(prefix="/v1/payments", tags=["payments"])

_MAGIC = {
    b"\xff\xd8\xff": ("jpg", "image/jpeg"),
    b"\x89PNG\r\n\x1a\n": ("png", "image/png"),
    b"%PDF-": ("pdf", "application/pdf"),
}


@router.get("/methods")
async def methods():
    return service.enabled_providers()


@router.post("", response_model=PaymentCreateOut, status_code=201,
             dependencies=[Depends(rate_limit("payment_create", 20, 60))])
async def create(data: PaymentCreateIn, user: CurrentUser, session: SessionDep):
    p = await service.create_payment(session, user, data.kind, data.target_id, data.provider)
    return PaymentCreateOut(payment=payment_out(p), checkout=service.checkout(p))


@router.get("", response_model=list[PaymentOut])
async def mine(user: CurrentUser, session: SessionDep, limit: int = Query(20, ge=1, le=100),
               offset: int = Query(0, ge=0, le=10_000)):
    rows = await session.scalars(select(Payment).where(Payment.user_id == user.id)
                                 .order_by(Payment.created_at.desc()).limit(limit).offset(offset))
    return [payment_out(p) for p in rows]


@router.get("/{payment_id}", response_model=PaymentCreateOut)
async def get_one(payment_id: str, user: CurrentUser, session: SessionDep):
    p = await session.get(Payment, payment_id)
    if not p or p.user_id != user.id:
        raise not_found("To'lov topilmadi")
    return PaymentCreateOut(payment=payment_out(p), checkout=service.checkout(p) if p.status == "pending" else {})


@router.post("/{payment_id}/receipt", response_model=PaymentOut,
             dependencies=[Depends(rate_limit("receipt", 10, 60))])
async def upload_receipt(payment_id: str, user: CurrentUser, session: SessionDep, file: UploadFile = File(...)):
    p = await service.lock_payment(session, payment_id)
    if not p or p.user_id != user.id:
        raise not_found("To'lov topilmadi")
    if p.provider != "manual" or p.status not in ("pending", "reviewing"):
        raise AppError(409, "bad_state", "Bu to'lovga chek yuklab bo'lmaydi")
    data = await file.read(get_settings().max_receipt_bytes + 1)
    if len(data) > get_settings().max_receipt_bytes:
        raise AppError(413, "file_too_large", "Fayl 10 MB dan oshmasligi kerak")
    kind = next((v for magic, v in _MAGIC.items() if data.startswith(magic)), None)
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        kind = ("webp", "image/webp")
    if not kind:
        raise AppError(400, "bad_file", "Faqat JPG, PNG, WEBP yoki PDF")
    key = f"receipts/{p.id}/{secrets.token_hex(8)}.{kind[0]}"
    await get_storage().put_bytes(key, data, kind[1])
    p.receipt_key, p.status, p.updated_at = key, "reviewing", utcnow()
    session.add(PaymentEvent(payment_id=p.id, source="user", event="receipt_uploaded", data={"key": key}))
    await session.commit()
    await notify_admin(f"🧾 Yangi chek: <b>{p.title}</b>\nSumma: {p.amount_tiyin // 100:,} so'm\nID: <code>{p.id}</code>")
    return payment_out(p)
