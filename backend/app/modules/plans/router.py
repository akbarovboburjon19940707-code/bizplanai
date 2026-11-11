import asyncio
import secrets
from typing import Literal

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import CurrentUser, SessionDep
from app.core.errors import AppError, not_found
from app.core.ratelimit import rate_limit
from app.engine.financial_engine import calculate_financial_model
from app.models import Plan
from app.modules.plans import service
from app.ai.images import sniff_image
from app.modules.plans.schemas import DownloadOut, ImageOut, PlanCreateIn, PlanInput, PlanOut, PreviewOut
from app.storage import get_storage

router = APIRouter(prefix="/v1/plans", tags=["plans"])


@router.post("/preview", response_model=PreviewOut, dependencies=[Depends(rate_limit("preview", 60, 60))])
async def preview(data: PlanInput):
    try:
        model = await asyncio.to_thread(calculate_financial_model, data.engine_payload())
    except (ValueError, ZeroDivisionError) as exc:
        raise AppError(400, "calculation_error", "Hisoblab bo'lmadi: kiritilgan qiymatlarni tekshiring") from exc
    return PreviewOut(indicators=model["indicators"], tables=model["tables"], context=model["context"])


@router.post("/images", response_model=ImageOut, status_code=201,
             dependencies=[Depends(rate_limit("plan_image", 20, 60))])
async def upload_image(user: CurrentUser, file: UploadFile = File(...)):
    """Muqova rasmi (JPG/PNG, 5 MB gacha). Qaytgan image_id PlanInput.rasm_id ga yoziladi; faqat egasi ishlata oladi."""
    limit = get_settings().max_plan_image_bytes
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise AppError(413, "file_too_large", "Rasm 5 MB dan oshmasligi kerak")
    kind = sniff_image(data)
    if not kind:
        raise AppError(400, "bad_file", "Faqat JPG yoki PNG rasm")
    image_id = f"{secrets.token_hex(16)}.{kind[0]}"
    await get_storage().put_bytes(service.image_key(user.id, image_id), data, kind[1])
    return ImageOut(image_id=image_id)


@router.post("", response_model=PlanOut, status_code=202, dependencies=[Depends(rate_limit("plan_create", 10, 60))])
async def create(data: PlanCreateIn, user: CurrentUser, session: SessionDep):
    plan = await service.create_plan(session, user, data.input, data.use_ai)
    await service.enqueue(plan.id)
    await session.refresh(plan)
    return service.to_out(plan)


@router.get("", response_model=list[PlanOut])
async def list_plans(user: CurrentUser, session: SessionDep,
                     limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=10_000)):
    rows = await session.scalars(select(Plan).where(Plan.user_id == user.id)
                                 .order_by(Plan.created_at.desc()).limit(limit).offset(offset))
    return [service.to_out(p) for p in rows]


async def _own_plan(session, user, plan_id: str) -> Plan:
    plan = await session.get(Plan, plan_id)
    if not plan or plan.user_id != user.id:
        raise not_found("Reja topilmadi")
    return plan


@router.get("/{plan_id}", response_model=PlanOut)
async def get_plan(plan_id: str, user: CurrentUser, session: SessionDep):
    return service.to_out(await _own_plan(session, user, plan_id))


@router.get("/{plan_id}/download", response_model=DownloadOut)
async def download(plan_id: str, user: CurrentUser, session: SessionDep,
                   format: Literal["docx", "xlsx", "pdf"] = "docx"):
    plan = await _own_plan(session, user, plan_id)
    if plan.status != "done":
        raise AppError(409, "not_ready", "Hujjat hali tayyor emas")
    if format == "pdf" and not plan.pdf_key:
        raise AppError(404, "pdf_unavailable", "Bu reja uchun PDF tayyorlanmagan. Word faylini yuklab oling.")
    key = {"docx": plan.word_key, "xlsx": plan.excel_key, "pdf": plan.pdf_key}[format]
    name = {"docx": "biznes reja.docx", "xlsx": "jadvallar.xlsx", "pdf": "biznes reja.pdf"}[format]
    name = f"{plan.title[:60]} - {name}"
    ttl = get_settings().download_url_ttl_seconds
    return DownloadOut(url=await get_storage().signed_url(key, name, ttl), expires_in=ttl)
