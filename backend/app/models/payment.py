from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (Index("ix_payments_status_created", "status", "created_at"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # subscription | catalog | plan_credit
    target_id: Mapped[str | None] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(255))
    amount_tiyin: Mapped[int] = mapped_column(Integer)
    provider: Mapped[str] = mapped_column(String(16))  # click | payme | manual
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|reviewing|paid|cancelled|rejected
    receipt_key: Mapped[str | None] = mapped_column(String(255))
    admin_note: Mapped[str | None] = mapped_column(String(500))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class PaymentEvent(TimestampMixin, Base):
    """Har bir provayder chaqiruvi va holat o'zgarishi: to'liq iz."""
    __tablename__ = "payment_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[str] = mapped_column(String(40), index=True)
    source: Mapped[str] = mapped_column(String(16))
    event: Mapped[str] = mapped_column(String(48))
    data: Mapped[dict | None] = mapped_column(JSON)


class ClickTransaction(TimestampMixin, Base):
    __tablename__ = "click_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # merchant_prepare_id
    payment_id: Mapped[str] = mapped_column(String(40), index=True)
    click_trans_id: Mapped[str] = mapped_column(String(40), unique=True)
    status: Mapped[str] = mapped_column(String(16), default="prepared")  # prepared|completed|cancelled


class PaymeTransaction(Base):
    __tablename__ = "payme_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payme_id: Mapped[str] = mapped_column(String(64), unique=True)
    payment_id: Mapped[str] = mapped_column(String(40), index=True)
    amount_tiyin: Mapped[int] = mapped_column(Integer)
    state: Mapped[int] = mapped_column(Integer, default=1)
    paycom_time: Mapped[int] = mapped_column(BigInteger, index=True)
    create_time: Mapped[int] = mapped_column(BigInteger)
    perform_time: Mapped[int] = mapped_column(BigInteger, default=0)
    cancel_time: Mapped[int] = mapped_column(BigInteger, default=0)
    reason: Mapped[int | None] = mapped_column(Integer)
