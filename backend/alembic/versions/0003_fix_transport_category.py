"""Move the 9 "Transport / Lizing" catalog products from xizmatlar to transport

The seed matched categories by exact label, so products labelled
"Transport / Lizing" fell back to the first category (xizmatlar). Only rows
still in xizmatlar are moved, so manual admin changes are kept.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-11 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TRANSPORT_IDS = (
    'bank_proj_13_2_avtomobillarni_yuvish_o_z_o_zi',
    'bank_proj_23_29_logistika_xizmatini_tashkil_e',
    'bank_proj_51_avtomobillarni_elektr_zaryadlash',
    'biz111_9_____________________6',
    'bplan2_25_AXMEDOV_AKMALJON__AVTOMOYKA',
    'bplan2_43_MATYOKUBOV_RUSLAN_RAJABBOYEVICH',
    'bplan2_48_TTL_Logistics',
    'bplan2_55',
    'howo-transport-lizing',
)

_products = sa.table('catalog_products', sa.column('id', sa.String), sa.column('category_key', sa.String))
_categories = sa.table('catalog_categories', sa.column('key', sa.String))


def upgrade() -> None:
    bind = op.get_bind()
    # Toza bazada (kategoriyalar hali seed qilinmagan) hech narsa qilinmaydi: seed endi to'g'ri yozadi
    if bind.execute(sa.select(_categories.c.key).where(_categories.c.key == 'transport')).first() is None:
        return
    op.execute(_products.update()
               .where(_products.c.id.in_(TRANSPORT_IDS), _products.c.category_key == 'xizmatlar')
               .values(category_key='transport'))


def downgrade() -> None:
    op.execute(_products.update()
               .where(_products.c.id.in_(TRANSPORT_IDS), _products.c.category_key == 'transport')
               .values(category_key='xizmatlar'))
