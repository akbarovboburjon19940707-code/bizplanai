"""Telegram: Mini App initData tekshiruvi (eski saytdan), bot orqali kirish va bot xabarlari."""
import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qsl

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import User

log = logging.getLogger(__name__)


def validate_init_data(init_data: str, bot_token: str, max_age: int) -> dict | None:
    """Telegram rasmiy algoritmi: HMAC-SHA256(key=HMAC("WebAppData", bot_token))."""
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except ValueError:
        return None
    received = pairs.pop("hash", None)
    if not received or not bot_token:
        return None
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received):
        return None
    try:
        auth_date = int(pairs.get("auth_date", "0"))
        user = json.loads(pairs.get("user", "{}"))
    except (ValueError, json.JSONDecodeError):
        return None
    if time.time() - auth_date > max_age or not user.get("id"):
        return None
    return user


async def get_or_create_telegram_user(session: AsyncSession, tg_user: dict) -> User:
    tg_id = str(tg_user["id"])
    user = await session.scalar(select(User).where(User.telegram_id == tg_id))
    if user is None:
        user = User(telegram_id=tg_id, first_name=(tg_user.get("first_name") or "")[:100],
                    last_name=(tg_user.get("last_name") or "")[:100],
                    telegram_username=(tg_user.get("username") or None))
        session.add(user)
        await session.flush()
    else:
        user.telegram_username = tg_user.get("username") or user.telegram_username
    return user


async def send_message(chat_id: str | int, text: str, reply_markup: dict | None = None) -> None:
    token = get_settings().telegram_bot_token
    if not token:
        return
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload)
    except httpx.HTTPError as exc:
        log.warning("telegram sendMessage xatosi: %s", exc)


async def notify_admin(text: str) -> None:
    chat = get_settings().telegram_admin_chat_id
    if chat:
        await send_message(chat, text)
