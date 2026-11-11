import hmac
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Header, Request
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import SessionDep
from app.core.errors import AppError
from app.core.redis import get_redis
from app.models import User
from app.modules.auth import password_reset
from app.modules.telegram.service import send_message

router = APIRouter(prefix="/v1/telegram", tags=["telegram"])
log = logging.getLogger(__name__)


def _keyboard() -> dict:
    url = get_settings().frontend_url.rstrip("/") + "/tg"
    return {"keyboard": [[{"text": "📋 Biznes reja yaratish", "web_app": {"url": url}}]], "resize_keyboard": True}


CONTACT_KEYBOARD = {"keyboard": [[{"text": "📱 Raqamimni yuborish", "request_contact": True}]],
                    "resize_keyboard": True, "one_time_keyboard": True}
RESET_REPLIES = {
    "verified": "✅ Raqam tasdiqlandi. Saytga qayting va yangi parolni kiriting.",
    "mismatch": "❌ Telegram raqamingiz saytdagi hisob raqamiga mos kelmadi (yoki bu raqam bilan parolli hisob yo'q).\n"
                "Saytda to'g'ri raqamni kiritib qaytadan urinib ko'ring yoki admin bilan bog'laning.",
    "foreign": "Faqat o'zingizning raqamingizni \"📱 Raqamimni yuborish\" tugmasi bilan yuboring.",
    "expired": "⏰ Tiklash so'rovi eskirgan. Saytda \"Parolni unutdingizmi?\" orqali qaytadan boshlang.",
}


@router.post("/webhook", include_in_schema=False)
async def webhook(request: Request, session: SessionDep,
                  x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None):
    expected = get_settings().telegram_webhook_header_token
    if not expected or not hmac.compare_digest(x_telegram_bot_api_secret_token or "", expected):
        raise AppError(403, "forbidden", "Webhook sirri noto'g'ri")
    update = await request.json()
    message = update.get("message") or {}
    text = (message.get("text") or "").strip()
    sender = message.get("from") or {}
    chat_id = (message.get("chat") or {}).get("id")
    contact = message.get("contact")
    if not sender.get("id") or chat_id is None or not (text or contact):
        return {"ok": True}

    if contact:  # parolni tiklash: Telegram tasdiqlagan raqam
        async def find_user(phone: str) -> str | None:
            return await session.scalar(select(User.id).where(User.phone == phone, User.is_active.is_(True),
                                                              User.password_hash.is_not(None)))
        result = await password_reset.verify_contact(chat_id, sender["id"], contact, find_user)
        keyboard = CONTACT_KEYBOARD if result == "foreign" else _keyboard()
        await send_message(chat_id, RESET_REPLIES[result], keyboard)
        return {"ok": True}

    name = sender.get("first_name") or "foydalanuvchi"
    if text.startswith("/start login_"):
        token = text[len("/start login_"):]
        r = get_redis()
        key = f"tglogin:{token}"
        raw = await r.get(key)
        if raw and json.loads(raw).get("status") == "pending":
            ttl = await r.ttl(key)
            tg_user = {k: sender.get(k) for k in ("id", "first_name", "last_name", "username")}
            await r.set(key, json.dumps({"status": "authenticated", "tg_user": tg_user}), ex=max(ttl, 30))
            await send_message(chat_id, f"✅ Salom, <b>{name}</b>! Saytga kirdingiz. Brauzerga qayting.", _keyboard())
        else:
            await send_message(chat_id, "⏰ Kirish havolasi eskirgan. Saytdan qaytadan urinib ko'ring.", _keyboard())
    elif text.startswith("/start reset_"):
        if await password_reset.bind_chat(text[len("/start reset_"):], chat_id):
            await send_message(chat_id, "🔐 Parolni tiklash.\n\nPastdagi <b>\"📱 Raqamimni yuborish\"</b> tugmasini bosing: "
                                        "Telegram raqamingiz saytdagi raqam bilan solishtiriladi.", CONTACT_KEYBOARD)
        else:
            await send_message(chat_id, RESET_REPLIES["expired"], _keyboard())
    elif text == "/start":
        await send_message(chat_id, f"👋 Salom, <b>{name}</b>!\n\nBizplanAI: bank talablariga mos biznes-reja "
                                    "bir necha daqiqada. Quyidagi tugmani bosing 👇", _keyboard())
    return {"ok": True}
