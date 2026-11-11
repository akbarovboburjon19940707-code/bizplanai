from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_id


class ContactMessage(TimestampMixin, Base):
    """Sayt "Aloqa" formasidan kelgan murojaat. Admin panelda ko'rinadi, Telegram'ga xabar ketadi."""

    __tablename__ = "contact_messages"
    __table_args__ = (Index("ix_contact_messages_status_created", "status", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20))
    topic: Mapped[str] = mapped_column(String(16))  # plan | payment | catalog | partnership | other
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="new")  # new | done
    admin_note: Mapped[str] = mapped_column(String(500), default="")
