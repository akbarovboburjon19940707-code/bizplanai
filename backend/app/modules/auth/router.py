import json
import secrets
import time

from fastapi import APIRouter, Cookie, Depends, Request, Response
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import SessionDep
from app.core.errors import AppError
from app.core.ratelimit import rate_limit
from app.core.redis import get_redis
from app.core.security import hash_password, verify_password, verify_totp
from app.models import User
from app.modules.auth import service
from app.modules.auth.schemas import (LoginIn, RefreshIn, RegisterIn, TelegramLoginInitOut,
                                      TelegramLoginPollOut, TelegramWebAppIn, TokenOut)
from app.modules.telegram.service import get_or_create_telegram_user, validate_init_data

router = APIRouter(prefix="/v1/auth", tags=["auth"])
TG_LOGIN_TTL = 300


@router.post("/register", response_model=TokenOut, status_code=201,
             dependencies=[Depends(rate_limit("register", 10, 60))])
async def register(data: RegisterIn, request: Request, response: Response, session: SessionDep):
    if await session.scalar(select(User.id).where(User.phone == data.phone)):
        raise AppError(409, "phone_taken", "Bu telefon raqam allaqachon ro'yxatdan o'tgan")
    user = User(phone=data.phone, password_hash=hash_password(data.password), first_name=data.first_name.strip())
    session.add(user)
    await session.flush()
    return await service.issue_session(session, response, request, user)


@router.post("/login", response_model=TokenOut, dependencies=[Depends(rate_limit("login", 20, 60))])
async def login(data: LoginIn, request: Request, response: Response, session: SessionDep):
    # Bitta raqamga parol tanlab ko'rishdan himoya (IP dan qat'i nazar)
    r = get_redis()
    key = f"rl:login_phone:{data.phone}:{int(time.time()) // 900}"
    if await r.incr(key) == 1:
        await r.expire(key, 901)
    if int(await r.get(key) or 0) > 10:
        raise AppError(429, "rate_limited", "Juda ko'p urinish. 15 daqiqadan so'ng qayta urinib ko'ring.")

    user = await session.scalar(select(User).where(User.phone == data.phone))
    if not user or not user.is_active or not verify_password(data.password, user.password_hash):
        raise AppError(401, "invalid_credentials", "Telefon raqam yoki parol noto'g'ri")
    if user.totp_secret:
        if not data.totp_code:
            raise AppError(401, "totp_required", "Autentifikator ilovasidagi 6 xonali kodni kiriting")
        if not verify_totp(user.totp_secret, data.totp_code):
            raise AppError(401, "totp_invalid", "Kod noto'g'ri yoki eskirgan")
    return await service.issue_session(session, response, request, user)


@router.post("/refresh", response_model=TokenOut, dependencies=[Depends(rate_limit("refresh", 60, 60))])
async def refresh(request: Request, response: Response, session: SessionDep,
                  body: RefreshIn | None = None, bp_refresh: str | None = Cookie(default=None)):
    raw = bp_refresh or (body.refresh_token if body else None)
    return await service.rotate_refresh(session, response, request, raw)


@router.post("/logout", status_code=204)
async def logout(response: Response, session: SessionDep, bp_refresh: str | None = Cookie(default=None)):
    await service.revoke_refresh(session, bp_refresh)
    service.clear_cookie(response)
    response.status_code = 204
    return response


@router.post("/telegram/webapp", response_model=TokenOut, dependencies=[Depends(rate_limit("tg_webapp", 30, 60))])
async def telegram_webapp(data: TelegramWebAppIn, request: Request, response: Response, session: SessionDep):
    s = get_settings()
    if not s.telegram_bot_token:
        raise AppError(503, "telegram_not_configured", "Telegram bot sozlanmagan")
    tg_user = validate_init_data(data.init_data, s.telegram_bot_token, s.telegram_initdata_max_age)
    if not tg_user:
        raise AppError(401, "telegram_invalid", "Telegram ma'lumotlari tasdiqlanmadi")
    user = await get_or_create_telegram_user(session, tg_user)
    return await service.issue_session(session, response, request, user)


@router.post("/telegram/login-init", response_model=TelegramLoginInitOut,
             dependencies=[Depends(rate_limit("tg_init", 10, 60))])
async def telegram_login_init():
    token = secrets.token_urlsafe(24)
    await get_redis().set(f"tglogin:{token}", json.dumps({"status": "pending"}), ex=TG_LOGIN_TTL)
    bot = get_settings().telegram_bot_name
    return TelegramLoginInitOut(token=token, bot_url=f"https://t.me/{bot}?start=login_{token}", expires_in=TG_LOGIN_TTL)


@router.get("/telegram/login-poll", response_model=TelegramLoginPollOut,
            dependencies=[Depends(rate_limit("tg_poll", 120, 60))])
async def telegram_login_poll(token: str, request: Request, response: Response, session: SessionDep):
    r = get_redis()
    key = f"tglogin:{token}"
    raw = await r.get(key)
    if not raw:
        return TelegramLoginPollOut(status="expired")
    state = json.loads(raw)
    if state.get("status") != "authenticated":
        return TelegramLoginPollOut(status="pending")
    if await r.delete(key) != 1:  # bir vaqtdagi ikkinchi so'rov sessiya olmaydi
        return TelegramLoginPollOut(status="expired")
    user = await get_or_create_telegram_user(session, state["tg_user"])
    return TelegramLoginPollOut(status="authenticated", session=await service.issue_session(session, response, request, user))
