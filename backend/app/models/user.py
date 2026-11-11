from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_id


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(150))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100), default="")
    last_name: Mapped[str] = mapped_column(String(100), default="")
    telegram_id: Mapped[str | None] = mapped_column(String(32), unique=True, index=True)
    telegram_username: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(16), default="user")  # user | admin
    totp_secret: Mapped[str | None] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    plan_credits: Mapped[int] = mapped_column(Integer, default=0)  # bir martalik pullik generatsiyalar
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)

    @property
    def has_password(self) -> bool:
        """Telegram orqali ro'yxatdan o'tganda parol yo'q (UserOut.has_password)."""
        return bool(self.password_hash)


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
    # Rotatsiyada yangi tokenning id si (logout va xavfsizlik yopishida bo'sh qoladi)
    replaced_by: Mapped[str | None] = mapped_column(String(36))
    user_agent: Mapped[str] = mapped_column(String(255), default="")
