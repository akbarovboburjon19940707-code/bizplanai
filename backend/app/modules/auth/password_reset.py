"""Parolni tiklash Telegram bot orqali (SMS'siz): foydalanuvchi botga o'z kontaktini yuboradi, Telegram tasdiqlagan
raqam hisobdagi raqamga mos kelsa, yangi parol qo'yiladi.

Oqim: init (telefon) -> t.me/<bot>?start=reset_<token> -> bot "Raqamni yuborish" tugmasi (request_contact) ->
kontakt (faqat o'z kontakti: contact.user_id == from.id) -> holat "verified" -> sayt yangi parolni yuboradi (complete).
Redis: pwreset:<token> = {phone, status, user_id}; pwreset_chat:<chat_id> = token. Token bir martalik, 10 daqiqa.
"""
import json
import secrets

from app.core.redis import get_redis
from app.modules.auth.schemas import normalize_phone

RESET_TTL = 600


def _key(token: str) -> str:
    return f"pwreset:{token}"


async def create(phone: str) -> str:
    token = secrets.token_urlsafe(24)
    await get_redis().set(_key(token), json.dumps({"phone": phone, "status": "pending"}), ex=RESET_TTL)
    return token


async def get(token: str) -> dict | None:
    if not token or len(token) > 64:
        return None
    raw = await get_redis().get(_key(token))
    return json.loads(raw) if raw else None


async def _save(token: str, state: dict) -> None:
    r = get_redis()
    ttl = await r.ttl(_key(token))
    await r.set(_key(token), json.dumps(state), ex=max(int(ttl or 0), 30))


async def bind_chat(token: str, chat_id: int | str) -> bool:
    """Bot /start reset_<token>: shu chatdan keladigan kontakt shu so'rovga tegishli."""
    state = await get(token)
    if not state or state.get("status") != "pending":
        return False
    await get_redis().set(f"pwreset_chat:{chat_id}", token, ex=RESET_TTL)
    return True


async def verify_contact(chat_id: int | str, sender_id: int, contact: dict, find_user) -> str:
    """Kontaktni tekshiradi. Natija: verified | mismatch | foreign | expired.
    `find_user(phone)` -> foydalanuvchi id yoki None (parolli hisob)."""
    r = get_redis()
    token = await r.get(f"pwreset_chat:{chat_id}")
    if isinstance(token, bytes):
        token = token.decode()
    state = await get(token) if token else None
    if not state or state.get("status") != "pending":
        return "expired"
    if contact.get("user_id") != sender_id:  # boshqa odamning kontaktini ulashish mumkin emas
        return "foreign"
    try:
        phone = normalize_phone(str(contact.get("phone_number") or ""))
    except ValueError:
        phone = ""
    user_id = await find_user(phone) if phone == state["phone"] else None
    if not user_id:
        state["status"] = "mismatch"
        await _save(token, state)
        await r.delete(f"pwreset_chat:{chat_id}")
        return "mismatch"
    state.update(status="verified", user_id=user_id)
    await _save(token, state)
    await r.delete(f"pwreset_chat:{chat_id}")
    return "verified"


async def consume(token: str) -> dict | None:
    """Tasdiqlangan so'rovni bir marta ishlatadi (parallel ikkinchi so'rov None oladi)."""
    state = await get(token)
    if not state or state.get("status") != "verified":
        return None
    if await get_redis().delete(_key(token)) != 1:
        return None
    return state
