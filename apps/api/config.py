from django.conf import settings
from ninja import NinjaAPI
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

from .auth import api_key_auth

TITLE = 'API'
VERSION = '1.0'



auth_api = NinjaAPI(
    title=TITLE,
    version=VERSION,
    auth=api_key_auth,
    urls_namespace='dasa_api',
    throttle=[
        AnonRateThrottle('10/s'),
        AuthRateThrottle('100/s'),
    ],
)
