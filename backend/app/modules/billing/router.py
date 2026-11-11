from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import SessionDep
from app.models import Tariff

router = APIRouter(prefix="/v1/tariffs", tags=["billing"])


class TariffOut(BaseModel):
    code: str
    name: str
    price_som: int
    duration_days: int
    daily_limit: int
    monthly_limit: int
    ai_enabled: bool


@router.get("", response_model=list[TariffOut])
async def list_tariffs(session: SessionDep):
    rows = (await session.scalars(select(Tariff).where(Tariff.is_active.is_(True)).order_by(Tariff.sort))).all()
    return [TariffOut(code=t.code, name=t.name, price_som=t.price_tiyin // 100, duration_days=t.duration_days,
                      daily_limit=t.daily_limit, monthly_limit=t.monthly_limit, ai_enabled=t.ai_enabled) for t in rows]


pricing_router = APIRouter(prefix="/v1/pricing", tags=["billing"])


class PricingOut(BaseModel):
    plan_credit_price_som: int  # bitta reja (AI bilan), POST /v1/payments kind=plan_credit


@pricing_router.get("", response_model=PricingOut)
async def pricing():
    return PricingOut(plan_credit_price_som=get_settings().plan_credit_price_som)
