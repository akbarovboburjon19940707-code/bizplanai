"""Bot ichidagi yordamchi: oddiy matnli xabarlarga javob. Suhbat tarixi Redis'da (oxirgi 10 xabar, 2 soat).
Javob HTML sifatida yuboriladi, shuning uchun model matni escape qilinadi; katalog rejalari havola bo'lib qo'shiladi."""
import html
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.service import MAX_MESSAGE_CHARS, MAX_TURNS, answer
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.ratelimit import hit
from app.core.redis import get_redis
from app.modules.telegram.service import send_chat_action, send_message

log = logging.getLogger(__name__)
HISTORY_TTL = 2 * 3600


def _esc(text: str) -> str:
    return html.escape(text, quote=False)


async def reply_in_chat(session: AsyncSession, chat_id: int | str, text: str) -> None:
    try:
        await hit(f"assistant:tg:{chat_id}", 20, 600)
        await hit(f"assistant:tgday:{chat_id}", 80, 86400)
    except AppError:
        await send_message(chat_id, "⏳ Savollar soni vaqtincha cheklangan. Biroz kuting yoki saytdagi Aloqa sahifasi orqali yozing.")
        return
    r = get_redis()
    key = f"assistant:tghist:{chat_id}"
    raw = await r.get(key)
    history = json.loads(raw) if raw else []
    history.append({"role": "user", "content": text[:MAX_MESSAGE_CHARS]})
    await send_chat_action(chat_id)
    try:
        reply = await answer(session, history)
    except Exception:  # bot hech qachon jim qolmasin; xato logda
        log.exception("yordamchi (telegram) xatosi")
        await send_message(chat_id, "Hozir javob bera olmadim. Birozdan so'ng qayta urinib ko'ring.")
        return
    history.append({"role": "assistant", "content": reply.text})
    await r.set(key, json.dumps(history[-MAX_TURNS:], ensure_ascii=False), ex=HISTORY_TTL)

    site = get_settings().frontend_url.rstrip("/")
    parts = [_esc(reply.text)]
    if reply.products:
        parts.append("\n".join(f'📄 <a href="{site}/katalog/{_esc(p.slug)}/">{_esc(p.title)}</a> · '
                               f"{p.price_tiyin // 100:,} so'm".replace(",", " ") for p in reply.products))
    if reply.handoff:
        parts.append(f'✉️ Aloqa: <a href="{site}/aloqa/">{site.replace("https://", "")}/aloqa</a>')
    await send_message(chat_id, "\n\n".join(parts))
