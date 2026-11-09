from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PaymentCreateIn(BaseModel):
    kind: Literal["subscription", "catalog", "plan_credit"]
    target_id: str | None = Field(default=None, max_length=120)
    provider: Literal["click", "payme", "manual"]


class PaymentOut(BaseModel):
    id: str
    kind: str
    target_id: str | None
    title: str
    amount_som: int
    provider: str
    status: str
    admin_note: str | None
    created_at: datetime
    paid_at: datetime | None


class PaymentCreateOut(BaseModel):
    payment: PaymentOut
    checkout: dict


def payment_out(p) -> PaymentOut:
    return PaymentOut(id=p.id, kind=p.kind, target_id=p.target_id, title=p.title, amount_som=p.amount_tiyin // 100,
                      provider=p.provider, status=p.status, admin_note=p.admin_note, created_at=p.created_at,
                      paid_at=p.paid_at)
