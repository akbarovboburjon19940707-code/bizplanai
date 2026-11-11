"""Admin: katalog rejasining PDF va muqova rasmini yuklash, rejani o'chirish, statik saytni qayta yig'ish.

Qoidalar (pul olinib, fayl berilmasligining oldini olish):
- yangi reja yashirin yaratiladi; PDF yuklanmaguncha faollashtirib bo'lmaydi (PATCH is_active=true -> 409 file_missing);
- sotilgan (huquq bor) yoki to'lovi ochiq rejani o'chirib bo'lmaydi: faqat yashirish (xaridorlar yuklab olishda davom etadi).
"""
import os
import re
import secrets
import tempfile
import unicodedata

import httpx
from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.deps import AdminUser, SessionDep
from app.core.errors import AppError, not_found
from app.core.ratelimit import hit
from app.models import AuditLog, CatalogProduct, Entitlement, Payment
from app.modules.catalog.router import IMAGE_PREFIX, image_key
from app.storage import get_storage

router = APIRouter()

_CYR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюяўқғҳ",
                ["a", "b", "v", "g", "d", "e", "yo", "j", "z", "i", "y", "k", "l", "m", "n", "o", "p", "r", "s", "t",
                 "u", "f", "x", "ts", "ch", "sh", "sh", "", "i", "", "e", "yu", "ya", "o", "q", "g", "h"], strict=True))
_IMAGE_MAGIC = {b"\x89PNG\r\n\x1a\n": ("png", "image/png"), b"\xff\xd8\xff": ("jpg", "image/jpeg")}


def slugify(title: str) -> str:
    text = "".join(_CYR.get(ch, ch) for ch in title.lower())
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:120] or "reja"


async def unique_slug(session, title: str) -> str:
    base = slugify(title)
    taken = set(await session.scalars(select(CatalogProduct.slug).where(CatalogProduct.slug.like(f"{base}%"))))
    if base not in taken:
        return base
    n = 2
    while f"{base}-{n}" in taken:
        n += 1
    return f"{base}-{n}"


def new_product_id() -> str:
    return f"p{secrets.token_hex(5)}"


def human_size(n: int) -> str:
    return f"{n / 1024 / 1024:.1f} MB" if n >= 1024 * 1024 else f"{max(n // 1024, 1)} KB"


async def _read_limited(file: UploadFile, limit: int, what: str) -> str:
    """Faylni xotiraga emas, vaqtinchalik faylga oqim bilan yozadi; chegara oshsa 413."""
    fd, path = tempfile.mkstemp(prefix="admin-upload-")
    size = 0
    try:
        with os.fdopen(fd, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    raise AppError(413, "file_too_large", f"{what} {limit // 1024 // 1024} MB dan oshmasligi kerak")
                out.write(chunk)
    except BaseException:
        os.remove(path)
        raise
    return path


async def _product(session, product_id: str) -> CatalogProduct:
    p = await session.get(CatalogProduct, product_id)
    if not p:
        raise not_found("Mahsulot topilmadi")
    return p


@router.post("/catalog/products/{product_id}/file")
async def upload_pdf(product_id: str, admin: AdminUser, session: SessionDep, file: UploadFile = File(...)):
    from app.modules.admin.router import admin_product_out

    p = await _product(session, product_id)
    path = await _read_limited(file, get_settings().max_catalog_pdf_bytes, "PDF")
    try:
        with open(path, "rb") as f:
            if f.read(5) != b"%PDF-":
                raise AppError(400, "bad_file", "Faqat PDF fayl yuklang")
        size = os.path.getsize(path)
        await get_storage().put_file(p.file_key, path, "application/pdf")
    finally:
        os.remove(path)
    p.file_size = human_size(size)
    session.add(AuditLog(actor_id=admin.id, action="catalog.file", entity="product", entity_id=p.id,
                         data={"key": p.file_key, "bytes": size}))
    await session.commit()
    return admin_product_out(p)


@router.post("/catalog/products/{product_id}/image")
async def upload_image(product_id: str, admin: AdminUser, session: SessionDep, file: UploadFile = File(...)):
    from app.modules.admin.router import admin_product_out

    p = await _product(session, product_id)
    limit = get_settings().max_catalog_image_bytes
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise AppError(413, "file_too_large", f"Rasm {limit // 1024 // 1024} MB dan oshmasligi kerak")
    kind = next((v for magic, v in _IMAGE_MAGIC.items() if data.startswith(magic)), None)
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        kind = ("webp", "image/webp")
    if not kind:
        raise AppError(400, "bad_file", "Faqat JPG, PNG yoki WEBP rasm")
    old = image_key(p.preview_image)
    key = f"{IMAGE_PREFIX}{p.id}-{secrets.token_hex(3)}.{kind[0]}"  # yangi nom: CDN/brauzer keshi eski rasmni bermasin
    await get_storage().put_bytes(key, data, kind[1])
    p.preview_image = key
    session.add(AuditLog(actor_id=admin.id, action="catalog.image", entity="product", entity_id=p.id, data={"key": key}))
    await session.commit()
    if old and old != key:
        await get_storage().delete(old)
    return admin_product_out(p)


@router.delete("/catalog/products/{product_id}", status_code=204)
async def delete_product(product_id: str, admin: AdminUser, session: SessionDep):
    p = await _product(session, product_id)
    sold = await session.scalar(select(func.count()).select_from(Entitlement).where(Entitlement.product_id == p.id))
    payments = await session.scalar(select(func.count()).select_from(Payment).where(
        Payment.kind == "catalog", Payment.target_id == p.id))
    if sold or payments:
        raise AppError(409, "product_sold", "Bu reja sotilgan yoki uning to'lovi bor: o'chirib bo'lmaydi, faqat yashiring. "
                       "Xaridorlar uni yuklab olishda davom etadi.", {"entitlements": sold, "payments": payments})
    keys = [p.file_key, image_key(p.preview_image)]
    await session.delete(p)
    session.add(AuditLog(actor_id=admin.id, action="catalog.delete", entity="product", entity_id=product_id,
                         data={"title": p.title, "slug": p.slug}))
    await session.commit()
    storage = get_storage()
    for key in filter(None, keys):
        await storage.delete(key)


class RebuildOut(BaseModel):
    triggered: bool


@router.post("/site/rebuild", response_model=RebuildOut)
async def rebuild_site(admin: AdminUser, session: SessionDep):
    """Katalog sahifalari statik: o'zgarishlar saytda ko'rinishi uchun bizplan-web qayta yig'iladi (Render Deploy Hook)."""
    url = get_settings().frontend_deploy_hook_url
    if not url:
        raise AppError(503, "not_configured", "Saytni yangilash sozlanmagan (FRONTEND_DEPLOY_HOOK_URL).")
    await hit("site_rebuild", 1, 120, "Sayt yaqinda yangilanishga yuborilgan. 2 daqiqadan so'ng qayta urinib ko'ring.")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            (await client.post(url)).raise_for_status()
    except httpx.HTTPError as exc:
        raise AppError(502, "rebuild_failed", "Render javob bermadi. Birozdan so'ng qayta urinib ko'ring.") from exc
    session.add(AuditLog(actor_id=admin.id, action="site.rebuild", entity="site", entity_id="web"))
    await session.commit()
    return RebuildOut(triggered=True)
