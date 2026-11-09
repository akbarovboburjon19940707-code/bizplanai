from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_id


class Tariff(Base):
    __tablename__ = "tariffs"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)  # basic | pro | enterprise
    name: Mapped[str] = mapped_column(String(64))
    price_tiyin: Mapped[int] = mapped_column(Integer, default=0)
    duration_days: Mapped[int] = mapped_column(Integer, default=30)
    daily_limit: Mapped[int] = mapped_column(Integer, default=0)
    monthly_limit: Mapped[int] = mapped_column(Integer, default=0)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Subscription(TimestampMixin, Base):
    __tablename__ = "subscriptions"
    __table_args__ = (Index("ix_subscriptions_user_ends", "user_id", "ends_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    tariff_code: Mapped[str] = mapped_column(ForeignKey("tariffs.code"))
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | revoked
    payment_id: Mapped[str | None] = mapped_column(String(40), index=True)


class UsageCounter(Base):
    """Kvota hisoblagichi. period_key: 'd:2026-11-09' yoki 'm:2026-11'."""
    __tablename__ = "usage_counters"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    period_key: Mapped[str] = mapped_column(String(16), primary_key=True)
    used: Mapped[int] = mapped_column(Integer, default=0)


class Entitlement(TimestampMixin, Base):
    """Katalog mahsulotiga egalik huquqi."""
    __tablename__ = "entitlements"
    __table_args__ = (Index("ix_entitlements_user_product", "user_id", "product_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    product_id: Mapped[str] = mapped_column(String(120))
    payment_id: Mapped[str | None] = mapped_column(String(40), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
