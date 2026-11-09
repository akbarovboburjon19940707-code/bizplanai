"""Bot webhookini ulash: TELEGRAM_BOT_TOKEN va TELEGRAM_WEBHOOK_SECRET muhitda bo'lishi kerak.
python scripts/set_telegram_webhook.py https://api.bizplanai.uz"""
import sys

import httpx

from app.core.config import get_settings

s = get_settings()
url = sys.argv[1].rstrip("/") + "/v1/telegram/webhook"
r = httpx.post(f"https://api.telegram.org/bot{s.telegram_bot_token}/setWebhook",
               json={"url": url, "secret_token": s.telegram_webhook_secret, "allowed_updates": ["message"]})
print(r.status_code, r.json())
