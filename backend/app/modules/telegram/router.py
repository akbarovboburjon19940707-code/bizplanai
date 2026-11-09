import hmac
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Header, Request

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.redis import get_redis
from app.modules.telegram.service import send_message

router = APIRouter(prefix="/v1/telegram", tags=["telegram"])
log = logging.getLogger(__name__)


def _keyboard() -> dict:
    url = get_settings().frontend_url.rstrip("/") + "/tg"
    return {"keyboard": [[{"text": "📋 Biznes reja yaratish", "web_app": {"url": url}}]], "resize_keyboard": True}


@router.post("/webhook", include_in_schema=False)
async def webhook(request: Request,
                  x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None):
    secret = get_settings().telegram_webhook_secret
    if not secret or not hmac.compare_digest(x_telegram_bot_api_secret_token or "", secret):
        raise AppError(403, "forbidden", "Webhook sirri noto'g'ri")
    update = await request.json()
    message = update.get("message") or {}
    text = (message.get("text") or "").strip()
    sender = message.get("from") or {}
    chat_id = (message.get("chat") or {}).get("id")
    if not text or not sender.get("id") or chat_id is None:
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
    elif text == "/start":
        await send_message(chat_id, f"👋 Salom, <b>{name}</b>!\n\nBizplanAI: bank talablariga mos biznes-reja "
                                    "bir necha daqiqada. Quyidagi tugmani bosing 👇", _keyboard())
    return {"ok": True}
