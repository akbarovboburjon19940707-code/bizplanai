from datetime import timedelta

from fastapi import Request, Response
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.base import new_id
from app.core.security import create_access_token, hash_token, new_refresh_token, utcnow
from app.models import RefreshToken, User
from app.modules.auth.schemas import TokenOut, UserOut

REFRESH_COOKIE = "bp_refresh"
REFRESH_PATH = "/v1/auth"
REFRESH_GRACE_SECONDS = 30


def _set_cookie(response: Response, raw: str) -> None:
    s = get_settings()
    response.set_cookie(
        REFRESH_COOKIE, raw, max_age=s.refresh_token_days * 86400, path=REFRESH_PATH,
        domain=s.cookie_domain, secure=s.cookie_secure, httponly=True, samesite="lax",
    )


def clear_cookie(response: Response) -> None:
    s = get_settings()
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_PATH, domain=s.cookie_domain)


async def issue_session(session: AsyncSession, response: Response, request: Request, user: User,
                        replaces: RefreshToken | None = None) -> TokenOut:
    s = get_settings()
    raw, digest = new_refresh_token()
    new_token = RefreshToken(
        id=new_id(), user_id=user.id, token_hash=digest,
        expires_at=utcnow() + timedelta(days=s.refresh_token_days),
        user_agent=(request.headers.get("user-agent") or "")[:255],
    )
    session.add(new_token)
    if replaces is not None:
        replaces.replaced_by = new_token.id
    user.last_login_at = utcnow()
    await session.commit()
    _set_cookie(response, raw)
    return TokenOut(
        access_token=create_access_token(user.id, user.role),
        expires_in=s.access_token_minutes * 60,
        user=UserOut.model_validate(user),
    )


async def _in_grace(session: AsyncSession, token: RefreshToken) -> bool:
    """Yaqinda rotatsiya qilingan token (bir vaqtdagi 2 tab yoki tarmoq takrori): o'g'irlik deb hisoblanmaydi.
    Shart: token logout/xavfsizlik bilan emas, rotatsiya bilan yopilgan va vorisi hali bekor qilinmagan."""
    if not token.replaced_by or token.revoked_at is None:
        return False
    if utcnow() - token.revoked_at > timedelta(seconds=REFRESH_GRACE_SECONDS):
        return False
    successor = await session.get(RefreshToken, token.replaced_by)
    return successor is not None and (successor.revoked_at is None or successor.replaced_by is not None)


async def rotate_refresh(session: AsyncSession, response: Response, request: Request, raw: str | None) -> TokenOut:
    if not raw:
        raise AppError(401, "unauthorized", "Refresh token yo'q")
    stmt = select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw))
    if session.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update()  # bir xil token bilan parallel so'rovlar navbat bilan o'tadi
    token = await session.scalar(stmt)
    if not token:
        raise AppError(401, "unauthorized", "Refresh token yaroqsiz")
    if token.revoked_at is not None and await _in_grace(session, token):
        user = await session.get(User, token.user_id)
        if not user or not user.is_active:
            raise AppError(401, "unauthorized", "Foydalanuvchi faol emas")
        return await issue_session(session, response, request, user)
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
    return await issue_session(session, response, request, user, replaces=token)


async def revoke_refresh(session: AsyncSession, raw: str | None) -> None:
    if not raw:
        return
    await session.execute(update(RefreshToken).where(RefreshToken.token_hash == hash_token(raw),
                                                     RefreshToken.revoked_at.is_(None)).values(revoked_at=utcnow()))
    await session.commit()
