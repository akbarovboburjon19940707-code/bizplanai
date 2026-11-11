from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field

from app.core.deps import CurrentUser, SessionDep
from app.core.errors import AppError
from app.core.ratelimit import rate_limit
from app.core.security import hash_password, verify_password
from app.models import Tariff
from app.modules.auth.schemas import UserOut
from app.modules.billing.service import FREE_TARIFF, active_subscription, usage

router = APIRouter(prefix="/v1/me", tags=["me"])


class SubscriptionOut(BaseModel):
    tariff_code: str
    tariff_name: str
    status: str  # free | active
    ends_at: str | None
    daily_limit: int
    monthly_limit: int
    daily_used: int
    monthly_used: int
    ai_enabled: bool


class MeOut(BaseModel):
    user: UserOut
    subscription: SubscriptionOut


class ProfileIn(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | Literal[""] | None = None  # "" = emailni o'chirish, None = o'zgartirmaslik


class PasswordIn(BaseModel):
    current_password: str | None = None
    new_password: str = Field(min_length=8, max_length=128)


@router.get("", response_model=MeOut)
async def me(user: CurrentUser, session: SessionDep):
    sub = await active_subscription(session, user.id)
    tariff = await session.get(Tariff, sub.tariff_code if sub else FREE_TARIFF)
    used = await usage(session, user.id)
    return MeOut(user=UserOut.model_validate(user), subscription=SubscriptionOut(
        tariff_code=tariff.code if tariff else FREE_TARIFF, tariff_name=tariff.name if tariff else "Bepul",
        status="active" if sub else "free", ends_at=sub.ends_at.isoformat() + "Z" if sub else None,
        daily_limit=tariff.daily_limit if tariff else 0, monthly_limit=tariff.monthly_limit if tariff else 0,
        ai_enabled=bool(tariff and tariff.ai_enabled), **used,
    ))


@router.patch("", response_model=UserOut)
async def update_profile(data: ProfileIn, user: CurrentUser, session: SessionDep):
    for field in ("first_name", "last_name", "email"):
        value = getattr(data, field)
        if value is not None:
            setattr(user, field, value.strip() if isinstance(value, str) else value)
    if data.email == "":
        user.email = None
    await session.commit()
    return UserOut.model_validate(user)


@router.post("/password", status_code=204, dependencies=[Depends(rate_limit("password", 10, 300))])
async def change_password(data: PasswordIn, user: CurrentUser, session: SessionDep):
    if user.password_hash and not verify_password(data.current_password or "", user.password_hash):
        raise AppError(400, "wrong_password", "Joriy parol noto'g'ri")
    user.password_hash = hash_password(data.new_password)
    await session.commit()
