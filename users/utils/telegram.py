import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)
def send_telegram(chat_id: str, message: str) -> bool:
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"  # Boleh pakai 'MarkdownV2' atau 'HTML'
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Gagal mengirim notifikasi Telegram: {e}")
        return False