"""refresh_tokens.replaced_by for concurrent-refresh grace window

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-10 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('refresh_tokens', schema=None) as batch_op:
        batch_op.add_column(sa.Column('replaced_by', sa.String(length=36), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('refresh_tokens', schema=None) as batch_op:
        batch_op.drop_column('replaced_by')
