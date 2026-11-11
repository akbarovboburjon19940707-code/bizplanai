"""Sayt yordamchisi: POST /v1/assistant/chat. Tarix brauzerda saqlanadi (serverda saqlanmaydi), har so'rovda
oxirgi 10 xabar yuboriladi. Cheklov: mehmon IP bo'yicha, kirgan foydalanuvchi id bo'yicha."""
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.assistant.service import MAX_MESSAGE_CHARS, MAX_TURNS, answer
from app.core.deps import OptionalUser, SessionDep
from app.core.errors import AppError
from app.core.ratelimit import client_ip, hit

router = APIRouter(prefix="/v1/assistant", tags=["assistant"])
LIMIT_MSG = "Savollar soni vaqtincha cheklangan. Biroz kuting yoki Aloqa sahifasi orqali yozing."


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatIn(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=2 * MAX_TURNS)


class ProductLink(BaseModel):
    id: str
    slug: str
    title: str
    price_som: int


class ChatOut(BaseModel):
    reply: str
    handoff: bool  # true: "Aloqa" tugmasini ko'rsatish
    products: list[ProductLink]


@router.post("/chat", response_model=ChatOut)
async def chat(data: ChatIn, request: Request, session: SessionDep, user: OptionalUser):
    if user:
        await hit(f"assistant:u:{user.id}", 40, 600, LIMIT_MSG)
    else:
        ip = client_ip(request)
        await hit(f"assistant:ip:{ip}", 15, 600, LIMIT_MSG)
        await hit(f"assistant:ipday:{ip}", 60, 86400, LIMIT_MSG)
    last = data.messages[-1]
    if last.role != "user" or len(last.content) > MAX_MESSAGE_CHARS:
        raise AppError(422, "validation_error", f"Savol {MAX_MESSAGE_CHARS} belgidan oshmasin")
    reply = await answer(session, [m.model_dump() for m in data.messages])
    return ChatOut(reply=reply.text, handoff=reply.handoff, products=[
        ProductLink(id=p.id, slug=p.slug, title=p.title, price_som=p.price_tiyin // 100) for p in reply.products])
