"""Aloqa formasi: POST /v1/contact. Spamdan himoya: IP bo'yicha rate limit, yashirin "website" maydoni (bot to'ldiradi),
bir xil raqamdan qisqa vaqtda takroriy xabar qabul qilinmaydi. Adminga Telegram xabari (HTML escape bilan)."""
import html
from functools import partial
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from app.core.deps import OptionalUser, SessionDep
from app.core.errors import AppError
from app.core.ratelimit import rate_limit
from app.core.redis import get_redis
from app.models import ContactMessage
from app.modules.auth.schemas import normalize_phone
from app.modules.telegram.service import notify_admin

router = APIRouter(prefix="/v1/contact", tags=["contact"])
_esc = partial(html.escape, quote=False)  # Telegram HTML: < > & yetarli, apostrof o'qilishi buzilmasin

Topic = Literal["plan", "payment", "catalog", "partnership", "other"]
TOPIC_LABELS = {"plan": "Biznes-reja yaratish", "payment": "To'lov", "catalog": "Tayyor rejalar katalogi",
                "partnership": "Hamkorlik", "other": "Boshqa"}
REPEAT_SECONDS = 60


class ContactIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str
    topic: Topic = "other"
    message: str = Field(min_length=10, max_length=2000)
    website: str = Field(default="", max_length=200)  # honeypot: odam ko'rmaydi, bot to'ldiradi

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        return " ".join(v.split())

    @field_validator("message")
    @classmethod
    def _message(cls, v: str) -> str:
        return v.strip()

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalize_phone(v)


class ContactOut(BaseModel):
    id: str
    status: str


@router.post("", response_model=ContactOut, status_code=201, dependencies=[Depends(rate_limit("contact", 5, 600))])
async def create(data: ContactIn, session: SessionDep, user: OptionalUser):
    if data.website:  # bot: muvaffaqiyat ko'rsatamiz, lekin hech narsa saqlamaymiz
        return ContactOut(id="ok", status="new")
    if len(data.name.strip()) < 2 or len(data.message.strip()) < 10:
        raise AppError(422, "validation_error", "Ism va xabarni to'liq yozing")
    r = get_redis()
    if not await r.set(f"contact:{data.phone}", "1", ex=REPEAT_SECONDS, nx=True):
        raise AppError(429, "rate_limited", "Xabaringiz qabul qilingan. Bir daqiqadan so'ng yana yozishingiz mumkin.")
    msg = ContactMessage(user_id=user.id if user else None, name=data.name, phone=data.phone, topic=data.topic,
                         message=data.message)
    session.add(msg)
    await session.commit()
    preview = data.message if len(data.message) <= 1500 else data.message[:1500] + "…"
    await notify_admin(
        "✉️ <b>Yangi murojaat</b> (sayt)\n"
        f"Mavzu: {_esc(TOPIC_LABELS[data.topic])}\n"
        f"Ism: {_esc(data.name)}\n"
        f"Telefon: {_esc(data.phone)}" + (" (ro'yxatdan o'tgan)" if user else "") + "\n\n"
        f"{_esc(preview)}"
    )
    return ContactOut(id=msg.id, status=msg.status)
