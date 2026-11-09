from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_id


class Plan(TimestampMixin, Base):
    __tablename__ = "plans"
    __table_args__ = (Index("ix_plans_user_created", "user_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    activity_type: Mapped[str] = mapped_column(String(32))
    input_json: Mapped[dict] = mapped_column(JSON)
    indicators_json: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16), default="queued", index=True)  # queued|running|done|failed
    error: Mapped[str | None] = mapped_column(Text)
    quota_source: Mapped[str] = mapped_column(String(16))  # free|subscription|credit
    ai_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_used: Mapped[bool] = mapped_column(Boolean, default=False)
    word_key: Mapped[str | None] = mapped_column(String(255))
    excel_key: Mapped[str | None] = mapped_column(String(255))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
