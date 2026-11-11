from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import func, or_, select

from app.core.deps import CurrentUser, SessionDep
from app.core.errors import AppError, not_found
from app.core.ratelimit import rate_limit
from app.core.redis import get_redis
from app.models import CatalogCategory, CatalogProduct, Entitlement
from app.modules.plans.schemas import DownloadOut
from app.storage import get_storage
from app.core.config import get_settings

router = APIRouter(prefix="/v1/catalog", tags=["catalog"])


class CategoryOut(BaseModel):
    key: str
    label: str
    icon: str
    count: int


class ProductOut(BaseModel):
    id: str
    slug: str
    category_key: str
    title: str
    description: str
    price_som: int
    file_size: str
    preview_image: str
    views: int
    downloads: int


class ProductPage(BaseModel):
    items: list[ProductOut]
    total: int
    limit: int
    offset: int


IMAGE_PREFIX = "catalog/images/"  # faqat shu papkadagi rasmlar imzolanadi (PDF yoki mijoz fayllari emas)
IMAGE_TTL = 3600


def image_key(preview_image: str) -> str | None:
    """Bazadagi qiymat (eski r2.dev URL yoki kalit) -> R2 kaliti. Ruxsat etilmagan yo'l bo'lsa None."""
    raw = (preview_image or "").strip()
    key = urlparse(raw).path.lstrip("/") if raw.startswith(("http://", "https://")) else raw.lstrip("/")
    if not key.startswith(IMAGE_PREFIX) or ".." in key or not key.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        return None
    return key


def product_out(p: CatalogProduct) -> ProductOut:
    # Bucket yopiq: rasm r2.dev dan emas, backend orqali (imzolangan havolaga yo'naltirish) beriladi
    image = (f"{get_settings().public_api_url.rstrip('/')}/v1/catalog/products/{p.id}/image"
             if image_key(p.preview_image) else "")
    return ProductOut(id=p.id, slug=p.slug, category_key=p.category_key, title=p.title, description=p.description,
                      price_som=p.price_tiyin // 100, file_size=p.file_size, preview_image=image,
                      views=p.views, downloads=p.downloads)


@router.get("/categories", response_model=list[CategoryOut])
async def categories(session: SessionDep):
    counts = dict((await session.execute(
        select(CatalogProduct.category_key, func.count()).where(CatalogProduct.is_active.is_(True))
        .group_by(CatalogProduct.category_key))).all())
    rows = await session.scalars(select(CatalogCategory).order_by(CatalogCategory.sort))
    return [CategoryOut(key=c.key, label=c.label, icon=c.icon, count=counts.get(c.key, 0)) for c in rows]


@router.get("/products", response_model=ProductPage)
async def products(session: SessionDep, category: str | None = None, q: str | None = Query(None, max_length=100),
                   limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=10_000)):
    cond = [CatalogProduct.is_active.is_(True)]
    if category:
        cond.append(CatalogProduct.category_key == category)
    if q:
        like = f"%{q.strip()}%"
        cond.append(or_(CatalogProduct.title.ilike(like), CatalogProduct.description.ilike(like)))
    total = await session.scalar(select(func.count()).select_from(CatalogProduct).where(*cond))
    rows = await session.scalars(select(CatalogProduct).where(*cond)
                                 .order_by(CatalogProduct.downloads.desc(), CatalogProduct.title).limit(limit).offset(offset))
    return ProductPage(items=[product_out(p) for p in rows], total=total or 0, limit=limit, offset=offset)


async def get_product(session, id_or_slug: str) -> CatalogProduct:
    p = await session.get(CatalogProduct, id_or_slug) or await session.scalar(
        select(CatalogProduct).where(CatalogProduct.slug == id_or_slug))
    if not p or not p.is_active:
        raise not_found("Mahsulot topilmadi")
    return p


@router.get("/products/{id_or_slug}", response_model=ProductOut)
async def product(id_or_slug: str, session: SessionDep):
    return product_out(await get_product(session, id_or_slug))


@router.get("/products/{id_or_slug}/image", status_code=302, dependencies=[Depends(rate_limit("catalog_image", 300, 60))],
            responses={302: {"description": "Imzolangan rasm havolasiga yo'naltirish"}})
async def product_image(id_or_slug: str, session: SessionDep):
    """Katalog muqova rasmi: yopiq bucket'dan 1 soatlik imzolangan havolaga 302 (brauzer 30 daqiqa keshlaydi)."""
    p = await get_product(session, id_or_slug)
    key = image_key(p.preview_image)
    if not key:
        raise not_found("Rasm topilmadi")
    url = await get_storage().signed_url(key, key.rsplit("/", 1)[-1], IMAGE_TTL, inline=True)
    return RedirectResponse(url, status_code=302, headers={"Cache-Control": "public, max-age=1800"})


@router.post("/products/{product_id}/view", status_code=204, dependencies=[Depends(rate_limit("view", 120, 60))])
async def view(product_id: str):
    # Ko'rishlar Redis'da yig'iladi, worker har 5 daqiqada bazaga yozadi (issiq qator qulflanmaydi)
    await get_redis().hincrby("catalog:views", product_id[:120], 1)


class OwnedOut(BaseModel):
    product_ids: list[str]


@router.get("/owned", response_model=OwnedOut)
async def owned(user: CurrentUser, session: SessionDep):
    """Foydalanuvchi sotib olgan katalog rejalari (sahifada darhol "Yuklab olish" ko'rsatish uchun)."""
    rows = await session.scalars(select(Entitlement.product_id).where(
        Entitlement.user_id == user.id, Entitlement.revoked_at.is_(None), Entitlement.product_id.is_not(None)).distinct())
    return OwnedOut(product_ids=sorted(rows))


@router.get("/products/{product_id}/download", response_model=DownloadOut)
async def download(product_id: str, user: CurrentUser, session: SessionDep):
    p = await get_product(session, product_id)
    owned = await session.scalar(select(Entitlement.id).where(
        Entitlement.user_id == user.id, Entitlement.product_id == p.id, Entitlement.revoked_at.is_(None)).limit(1))
    if not owned:
        raise AppError(403, "not_purchased", "Avval ushbu rejani sotib oling")
    storage = get_storage()
    if not await storage.exists(p.file_key):
        raise AppError(404, "file_missing", "Fayl hozircha mavjud emas. Administrator xabardor qilindi.")
    p.downloads += 1
    await session.commit()
    ttl = get_settings().download_url_ttl_seconds
    return DownloadOut(url=await storage.signed_url(p.file_key, f"{p.title[:80]}.pdf", ttl), expires_in=ttl)
