"""tariffs: paid-only documents (free 0), Standart 200 000 so'm 3/10, Premium 10/100 (business decision 2026-11-12)

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-12 01:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0006'
down_revision: Union[str, Sequence[str], None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

tariffs = sa.table("tariffs", sa.column("code", sa.String), sa.column("daily_limit", sa.Integer),
                   sa.column("monthly_limit", sa.Integer))
NEW = {"basic": (0, 0), "pro": (3, 10), "enterprise": (10, 100)}
OLD = {"basic": (3, 10), "pro": (15, 50), "enterprise": (50, 500)}


def _apply(values: dict[str, tuple[int, int]]) -> None:
    for code, (daily, monthly) in values.items():
        op.execute(tariffs.update().where(tariffs.c.code == code).values(daily_limit=daily, monthly_limit=monthly))


prices = sa.table("tariffs", sa.column("code", sa.String), sa.column("price_tiyin", sa.Integer))


def upgrade() -> None:
    _apply(NEW)
    op.execute(prices.update().where(prices.c.code == "pro").values(price_tiyin=200_000_00))


def downgrade() -> None:
    _apply(OLD)
    op.execute(prices.update().where(prices.c.code == "pro").values(price_tiyin=50_000_00))
