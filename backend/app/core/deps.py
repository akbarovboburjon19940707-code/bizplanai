from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import decode_token
from app.db.session import get_session
from app.models import User

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def _user_from_header(session: AsyncSession, authorization: str | None) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    payload = decode_token(authorization[7:].strip(), "access")
    if not payload:
        return None
    user = await session.get(User, payload["sub"])
    if not user or not user.is_active:
        return None
    return user


async def current_user(session: SessionDep, authorization: Annotated[str | None, Header()] = None) -> User:
    user = await _user_from_header(session, authorization)
    if not user:
        raise AppError(401, "unauthorized", "Avtorizatsiya talab qilinadi")
    return user


async def optional_user(session: SessionDep, authorization: Annotated[str | None, Header()] = None) -> User | None:
    return await _user_from_header(session, authorization)


async def admin_user(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role != "admin":
        raise AppError(403, "forbidden", "Faqat administrator uchun")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
OptionalUser = Annotated[User | None, Depends(optional_user)]
AdminUser = Annotated[User, Depends(admin_user)]
