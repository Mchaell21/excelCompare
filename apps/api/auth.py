import hmac

from django.conf import settings
from ninja.security import APIKeyHeader

API_KEY_HEADER = 'X-API-Key'

class DasaApiKey(APIKeyHeader):
    param_name = API_KEY_HEADER

    def authenticate(self, request, key):
        expected = (getattr(settings, 'SECRET_API_KEY', '') or '').strip()
        if not expected:
            return False
        if not key:
            return False
        return hmac.compare_digest(
            str(key).encode('utf-8'), expected.encode('utf-8'))

api_key_auth = DasaApiKey()
