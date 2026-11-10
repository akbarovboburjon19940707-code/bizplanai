"""Bot webhookini ulash. TELEGRAM_BOT_TOKEN va TELEGRAM_WEBHOOK_SECRET muhitda bo'lishi kerak.

Render Shell'da (/app ichida), ikkala usul ham ishlaydi:
    python scripts/set_telegram_webhook.py https://api.bizplanai.uz
    python -m scripts.set_telegram_webhook https://api.bizplanai.uz
"""
import sys
from pathlib import Path

# `python scripts/x.py` da sys.path[0] = scripts/, shuning uchun `app` paketi topilmaydi: ildizni qo'shamiz.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402

from app.core.config import get_settings  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].startswith("https://"):
        print("Foydalanish: python scripts/set_telegram_webhook.py https://<api-domen>", file=sys.stderr)
        return 2
    s = get_settings()
    missing = [k for k, v in (("TELEGRAM_BOT_TOKEN", s.telegram_bot_token),
                              ("TELEGRAM_WEBHOOK_SECRET", s.telegram_webhook_secret)) if not v]
    if missing:
        print(f"Muhitda yo'q: {', '.join(missing)} (Render > Environment Groups)", file=sys.stderr)
        return 1
    url = sys.argv[1].rstrip("/") + "/v1/telegram/webhook"
    r = httpx.post(f"https://api.telegram.org/bot{s.telegram_bot_token}/setWebhook", timeout=15,
                   json={"url": url, "secret_token": s.telegram_webhook_header_token, "allowed_updates": ["message"]})
    body = r.json()
    print(r.status_code, body.get("description", body))  # tokenni chiqarmaymiz
    return 0 if body.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
