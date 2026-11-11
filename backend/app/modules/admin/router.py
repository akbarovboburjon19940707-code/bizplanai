from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select

from app.core.deps import AdminUser, SessionDep
from app.core.errors import AppError, not_found
from app.core.security import utcnow
from app.models import AuditLog, CatalogCategory, CatalogProduct, Payment, Plan, Subscription, User
from app.modules.auth.schemas import UserOut
from app.modules.catalog.router import ProductOut, product_out
from app.modules.payments.schemas import PaymentOut, payment_out
from app.modules.payments.service import lock_payment, mark_cancelled, mark_paid
from app.modules.plans.schemas import DownloadOut
from app.storage import get_storage

router = APIRouter(prefix="/v1/admin", tags=["admin"])


class AdminPaymentOut(PaymentOut):
    user_id: str
    user_phone: str | None = None  # admin chekni kimdan kelganini ko'rishi uchun
    user_name: str = ""
    has_receipt: bool


class AdminProductOut(ProductOut):
    is_active: bool
    file_key: str


class AdminProductPage(BaseModel):
    items: list[AdminProductOut]
    total: int
    limit: int
    offset: int


def admin_product_out(p: CatalogProduct) -> AdminProductOut:
    return AdminProductOut(**product_out(p).model_dump(), is_active=p.is_active, file_key=p.file_key)


class NoteIn(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class ProductIn(BaseModel):
    id: str = Field(min_length=2, max_length=120, pattern=r"^[A-Za-z0-9_\-]+$")
    slug: str = Field(min_length=2, max_length=200, pattern=r"^[a-z0-9\-]+$")
    category_key: str
    title: str = Field(min_length=2, max_length=255)
    description: str = ""
    price_som: int = Field(gt=0, le=100_000_000)
    file_key: str = Field(min_length=3, max_length=255)
    preview_image: str = ""
    file_size: str = ""


class ProductPatch(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    price_som: int | None = Field(default=None, gt=0, le=100_000_000)
    file_key: str | None = Field(default=None, max_length=255)
    preview_image: str | None = None
    category_key: str | None = None
    is_active: bool | None = None


@router.get("/stats")
async def stats(_: AdminUser, session: SessionDep):
    day_ago = utcnow() - timedelta(days=1)
    paid_sum = await session.scalar(select(func.coalesce(func.sum(Payment.amount_tiyin), 0)).where(Payment.status == "paid"))
    return {
        "users_total": await session.scalar(select(func.count()).select_from(User)),
        "users_24h": await session.scalar(select(func.count()).select_from(User).where(User.created_at >= day_ago)),
        "plans_total": await session.scalar(select(func.count()).select_from(Plan)),
        "plans_24h": await session.scalar(select(func.count()).select_from(Plan).where(Plan.created_at >= day_ago)),
        "plans_failed_24h": await session.scalar(select(func.count()).select_from(Plan).where(
            Plan.created_at >= day_ago, Plan.status == "failed")),
        "payments_reviewing": await session.scalar(select(func.count()).select_from(Payment).where(Payment.status == "reviewing")),
        "revenue_som": int(paid_sum or 0) // 100,
        "active_subscriptions": await session.scalar(select(func.count()).select_from(Subscription).where(
            Subscription.status == "active", Subscription.ends_at > utcnow())),
    }


@router.get("/payments", response_model=list[AdminPaymentOut])
async def payments(_: AdminUser, session: SessionDep,
                   status: Literal["pending", "reviewing", "paid", "cancelled", "rejected"] | None = None,
                   limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    stmt = select(Payment).order_by(Payment.created_at.desc()).limit(limit).offset(offset)
    if status:
        stmt = stmt.where(Payment.status == status)
    rows = list(await session.scalars(stmt))
    owners = {u.id: u for u in await session.scalars(select(User).where(User.id.in_({p.user_id for p in rows})))} if rows else {}
    out = []
    for p in rows:
        u = owners.get(p.user_id)
        name = " ".join(x for x in (u.first_name, u.last_name) if x) if u else ""
        out.append(AdminPaymentOut(**payment_out(p).model_dump(), user_id=p.user_id, user_phone=u.phone if u else None,
                                   user_name=name, has_receipt=bool(p.receipt_key)))
    return out


@router.get("/payments/{payment_id}/receipt", response_model=DownloadOut)
async def receipt(payment_id: str, _: AdminUser, session: SessionDep):
    p = await session.get(Payment, payment_id)
    if not p or not p.receipt_key:
        raise not_found("Chek topilmadi")
    # inline: admin chekni brauzerda ko'radi (yuklab olinmaydi). Fayl turi yuklashda magic bytes bilan tekshirilgan.
    url = await get_storage().signed_url(p.receipt_key, p.receipt_key.rsplit("/", 1)[-1], 300, inline=True)
    return DownloadOut(url=url, expires_in=300)


@router.post("/payments/{payment_id}/approve", response_model=PaymentOut)
async def approve(payment_id: str, data: NoteIn, admin: AdminUser, session: SessionDep):
    p = await lock_payment(session, payment_id)
    if not p:
        raise not_found("To'lov topilmadi")
    if p.provider != "manual" or p.status not in ("pending", "reviewing"):
        raise AppError(409, "bad_state", "Faqat ko'rib chiqilayotgan qo'lda to'lovni tasdiqlash mumkin")
    await mark_paid(session, p, "admin", actor_id=admin.id, note=data.note)
    await session.commit()
    return payment_out(p)


@router.post("/payments/{payment_id}/reject", response_model=PaymentOut)
async def reject(payment_id: str, data: NoteIn, admin: AdminUser, session: SessionDep):
    p = await lock_payment(session, payment_id)
    if not p:
        raise not_found("To'lov topilmadi")
    if p.provider != "manual":
        raise AppError(409, "bad_state", "Click/Payme to'lovlari provayder orqali bekor qilinadi")
    await mark_cancelled(session, p, "admin", new_status="rejected", actor_id=admin.id, note=data.note)
    await session.commit()
    return payment_out(p)


@router.get("/users", response_model=list[UserOut])
async def users(_: AdminUser, session: SessionDep, q: str | None = Query(None, max_length=100),
                limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    stmt = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(User.phone.ilike(like), User.first_name.ilike(like), User.telegram_username.ilike(like)))
    return [UserOut.model_validate(u) for u in await session.scalars(stmt)]


@router.get("/catalog/products", response_model=AdminProductPage)
async def list_products(_: AdminUser, session: SessionDep, q: str | None = Query(None, max_length=100),
                        category: str | None = None, active: bool | None = None,
                        limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0, le=10_000)):
    """Admin katalogi: yashirilgan (`is_active=false`) mahsulotlar ham ko'rinadi, shunda ularni qayta ochish mumkin."""
    cond = []
    if q:
        like = f"%{q.strip()}%"
        cond.append(or_(CatalogProduct.title.ilike(like), CatalogProduct.id.ilike(like), CatalogProduct.slug.ilike(like)))
    if category:
        cond.append(CatalogProduct.category_key == category)
    if active is not None:
        cond.append(CatalogProduct.is_active.is_(active))
    total = await session.scalar(select(func.count()).select_from(CatalogProduct).where(*cond))
    rows = await session.scalars(select(CatalogProduct).where(*cond).order_by(CatalogProduct.title).limit(limit).offset(offset))
    return AdminProductPage(items=[admin_product_out(p) for p in rows], total=total or 0, limit=limit, offset=offset)


@router.post("/catalog/products", response_model=AdminProductOut, status_code=201)
async def add_product(data: ProductIn, admin: AdminUser, session: SessionDep):
    if not await session.get(CatalogCategory, data.category_key):
        raise AppError(400, "bad_category", "Kategoriya topilmadi")
    if await session.get(CatalogProduct, data.id):
        raise AppError(409, "exists", "Bunday ID mavjud")
    p = CatalogProduct(**data.model_dump(exclude={"price_som"}), price_tiyin=data.price_som * 100)
    session.add(p)
    session.add(AuditLog(actor_id=admin.id, action="catalog.add", entity="product", entity_id=p.id))
    await session.commit()
    return admin_product_out(p)


@router.patch("/catalog/products/{product_id}", response_model=AdminProductOut)
async def patch_product(product_id: str, data: ProductPatch, admin: AdminUser, session: SessionDep):
    p = await session.get(CatalogProduct, product_id)
    if not p:
        raise not_found("Mahsulot topilmadi")
    changes = data.model_dump(exclude_unset=True)
    if "category_key" in changes and not await session.get(CatalogCategory, changes["category_key"]):
        raise AppError(400, "bad_category", "Kategoriya topilmadi")
    if "price_som" in changes:
        p.price_tiyin = changes.pop("price_som") * 100
    for k, v in changes.items():
        setattr(p, k, v)
    session.add(AuditLog(actor_id=admin.id, action="catalog.update", entity="product", entity_id=p.id, data=data.model_dump(exclude_unset=True)))
    await session.commit()
    return admin_product_out(p)
