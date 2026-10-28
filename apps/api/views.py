from django.http import HttpRequest
from ninja.errors import HttpError
from config.utils.exceptions import DomainError

from .config import auth_api
from .schemas import ApiMessage
from .service import AuthService



@auth_api.get('/ping', response=ApiMessage)
def ping(request: HttpRequest):
    return {
        'status': 'success',
        'message': 'Sistem Titip siap menerima webhook DASA.',
        'data': None,
    }