from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CatalogCategory(Base):
    __tablename__ = "catalog_categories"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(120))
    icon: Mapped[str] = mapped_column(String(16), default="")
    sort: Mapped[int] = mapped_column(Integer, default=0)


class CatalogProduct(TimestampMixin, Base):
    __tablename__ = "catalog_products"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True)
    category_key: Mapped[str] = mapped_column(ForeignKey("catalog_categories.key"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    price_tiyin: Mapped[int] = mapped_column(Integer)
    file_key: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[str] = mapped_column(String(32), default="")
    preview_image: Mapped[str] = mapped_column(String(500), default="")
    views: Mapped[int] = mapped_column(Integer, default=0)
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
