import asyncio
import logging
import os
import tempfile

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.appendix import append_ai_chapter
from app.ai.service import generate_sections
from app.core.config import get_settings
from app.core.security import utcnow
from app.db.session import sessionmaker
from app.engine.excel_generator import generate_excel_report
from app.engine.financial_engine import calculate_financial_model
from app.engine.word_generator import generate_word_report
from app.models import Plan, User
from app.modules.billing.service import consume_quota, refund_quota
from app.modules.plans.schemas import PlanInput, PlanOut
from app.storage import get_storage

log = logging.getLogger(__name__)
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def to_out(p: Plan) -> PlanOut:
    return PlanOut(id=p.id, title=p.title, activity_type=p.activity_type, status=p.status, error=p.error,
                   quota_source=p.quota_source, ai_requested=p.ai_requested, ai_used=p.ai_used,
                   indicators=p.indicators_json, created_at=p.created_at, finished_at=p.finished_at)


async def create_plan(session: AsyncSession, user: User, data: PlanInput, use_ai: bool) -> Plan:
    grant = await consume_quota(session, user)
    plan = Plan(user_id=user.id, title=data.loyiha_nomi, activity_type=data.faoliyat_turi,
                input_json={"engine": data.engine_payload(), "quota_keys": list(grant.period_keys)},
                status="queued", quota_source=grant.source, ai_requested=use_ai and grant.ai_allowed)
    session.add(plan)
    await session.commit()
    return plan


async def enqueue(plan_id: str) -> None:
    if get_settings().job_mode == "inline":
        await run_generation(plan_id)
        return
    from app.workers.queue import get_pool

    pool = await get_pool()
    await pool.enqueue_job("generate_plan", plan_id, _job_id=f"plan:{plan_id}")


def _render_files(payload: dict, workdir: str) -> tuple[dict, str, str]:
    model = calculate_financial_model(payload)
    word = os.path.join(workdir, "biznes_reja.docx")
    excel = os.path.join(workdir, "jadvallar.xlsx")
    generate_word_report(model, word)
    generate_excel_report(model, excel)
    return model, word, excel


async def run_generation(plan_id: str) -> None:
    """Worker vazifasi: hisob, ixtiyoriy AI, Word + Excel, saqlash. Xatoda kvota qaytariladi."""
    async with sessionmaker()() as session:
        plan = await session.get(Plan, plan_id)
        if not plan or plan.status not in ("queued", "running"):
            return
        plan.status = "running"
        await session.commit()
        try:
            payload = plan.input_json["engine"]
            with tempfile.TemporaryDirectory() as workdir:
                model, word, excel = await asyncio.to_thread(_render_files, payload, workdir)
                if plan.ai_requested:
                    sections = await generate_sections(model["context"], model["indicators"])
                    if sections:
                        await asyncio.to_thread(append_ai_chapter, word, sections)
                        plan.ai_used = True
                storage = get_storage()
                base = f"plans/{plan.user_id}/{plan.id}"
                await storage.put_file(f"{base}/biznes_reja.docx", word, DOCX)
                await storage.put_file(f"{base}/jadvallar.xlsx", excel, XLSX)
            plan.word_key, plan.excel_key = f"{base}/biznes_reja.docx", f"{base}/jadvallar.xlsx"
            plan.indicators_json = _jsonable(model["indicators"])
            plan.status, plan.finished_at = "done", utcnow()
            await session.commit()
        except Exception:  # noqa: BLE001 - har qanday xato foydalanuvchiga kvotani qaytaradi
            log.exception("plan generatsiyasi xatosi plan_id=%s", plan_id)
            await session.rollback()
            plan = await session.get(Plan, plan_id)
            plan.status, plan.error, plan.finished_at = "failed", "Hujjat yaratishda xatolik", utcnow()
            await refund_quota(session, plan.user_id, plan.quota_source, tuple(plan.input_json.get("quota_keys", [])))
            await session.commit()


def _jsonable(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, (int, float, str, bool)) or v is None:
            out[k] = v
        else:
            out[k] = str(v)
    return out
