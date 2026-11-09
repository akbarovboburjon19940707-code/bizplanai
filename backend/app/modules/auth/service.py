from datetime import timedelta

from fastapi import Request, Response
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import create_access_token, hash_token, new_refresh_token, utcnow
from app.models import RefreshToken, User
from app.modules.auth.schemas import TokenOut, UserOut

REFRESH_COOKIE = "bp_refresh"
REFRESH_PATH = "/v1/auth"


def _set_cookie(response: Response, raw: str) -> None:
    s = get_settings()
    response.set_cookie(
        REFRESH_COOKIE, raw, max_age=s.refresh_token_days * 86400, path=REFRESH_PATH,
        domain=s.cookie_domain, secure=s.cookie_secure, httponly=True, samesite="lax",
    )


def clear_cookie(response: Response) -> None:
    s = get_settings()
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_PATH, domain=s.cookie_domain)


async def issue_session(session: AsyncSession, response: Response, request: Request, user: User) -> TokenOut:
    s = get_settings()
    raw, digest = new_refresh_token()
    session.add(RefreshToken(
        user_id=user.id, token_hash=digest,
        expires_at=utcnow() + timedelta(days=s.refresh_token_days),
        user_agent=(request.headers.get("user-agent") or "")[:255],
    ))
    user.last_login_at = utcnow()
    await session.commit()
    _set_cookie(response, raw)
    return TokenOut(
        access_token=create_access_token(user.id, user.role),
        expires_in=s.access_token_minutes * 60,
        user=UserOut.model_validate(user),
    )


async def rotate_refresh(session: AsyncSession, response: Response, request: Request, raw: str | None) -> TokenOut:
    if not raw:
        raise AppError(401, "unauthorized", "Refresh token yo'q")
    token = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw)))
    if not token:
        raise AppError(401, "unauthorized", "Refresh token yaroqsiz")
    if token.revoked_at is not None:
        # Qayta ishlatilgan token: o'g'irlangan bo'lishi mumkin, barcha sessiyalar yopiladi
        await session.execute(update(RefreshToken).where(RefreshToken.user_id == token.user_id,
                                                         RefreshToken.revoked_at.is_(None)).values(revoked_at=utcnow()))
        await session.commit()
        clear_cookie(response)
        raise AppError(401, "token_reused", "Sessiya xavfsizlik sababli yopildi. Qaytadan kiring.")
    if token.expires_at < utcnow():
        raise AppError(401, "unauthorized", "Sessiya muddati tugagan")
    user = await session.get(User, token.user_id)
    if not user or not user.is_active:
        raise AppError(401, "unauthorized", "Foydalanuvchi faol emas")
    token.revoked_at = utcnow()
    return await issue_session(session, response, request, user)


async def revoke_refresh(session: AsyncSession, raw: str | None) -> None:
    if not raw:
        return
    await session.execute(update(RefreshToken).where(RefreshToken.token_hash == hash_token(raw),
                                                     RefreshToken.revoked_at.is_(None)).values(revoked_at=utcnow()))
    await session.commit()
