import json
import traceback
from typing import Any
import requests
from django.conf import settings
from django.http import HttpRequest

SENSITIVE_KEYS = {'password', 'password_confirm', 'token', 'access_token', 'refresh_token', 'secret', 'credit_card', 'cvv', 'csr', 'csrf', 'csrfmiddlewaretoken'}

def sanitize_data(data):
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if key.lower() in SENSITIVE_KEYS:
                cleaned[key] = "***Sensor***"
            else: 
                cleaned[key] = sanitize_data(value)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    return data

def get_sanitized_body(request: HttpRequest):
    if not request.body:
        return "Kosong"

    content_type = request.META.get('CONTENT_TYPE', '')
    try:
        # Jika request berupa JSON
        if 'application/json' in content_type:
            body_data = json.loads(request.body.decode('utf-8'))
            sanitized_data = sanitize_data(body_data)
            return json.dumps(sanitized_data, indent=2)

        # Jika request berupa Form Submit (POST biasa)
        elif 'application/x-www-form-urlencoded' in content_type or 'multipart/form-data' in content_type:
            post_data = request.POST.dict()
            sanitized_data = sanitize_data(post_data)
            return json.dumps(sanitized_data, indent=2)

        # Tipe payload lain
        return request.body.decode('utf-8')[:1000]
    except Exception:
        return "Tidak dapat mengambil data body."

def capture_and_send_to_discord( exception, is_handled=False, custom_title=None, request=None):
    body_text = get_sanitized_body(request) if request else ""
    stack_trace = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    truncated_trace = stack_trace[-1000:] if len(stack_trace) > 1000 else stack_trace

    status_tag = "⚠️ Handled Exception" if is_handled else "🚨 Unhandled Exception (500)"
    title = custom_title or f"{status_tag}: {type(exception).__name__}"
    color = 16753920 if is_handled else 15158332  # Orange untuk Handled, Merah untuk Unhandled (500)

    user_info = getattr(request, 'user', 'Anonymous')
    payload = {
        "embeds": [{
            "title": title,
            "description": f"**Message:** `{str(exception)}`",
            "color": color,
            "fields": [
                {
                    "name": "📌 Request Info",
                    "value": f"**Path:** `{request.path if request else "[External]"}`\n**Method:** `{request.method if request else "[External]"}`\n**User:** `{user_info}`",
                    "inline": False
                },
                {
                    "name": "📦 Request Body (Sanitized)",
                    "value": f"```json\n{body_text[:1000]}\n```",
                    "inline": False
                },
                {
                    "name": "🔍 Stack Trace (Tail)",
                    "value": f"```python\n{truncated_trace}\n```",
                    "inline": False
                }
            ]
        }]
    }

    webhook_url = getattr(settings, 'DISCORD_WEBHOOK_URL', None)
    if webhook_url:
        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"Failed to send log to Discord: {e}")

class DiscordErrorNotifierMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        capture_and_send_to_discord(request=request, exception=exception, is_handled=False)
        return None