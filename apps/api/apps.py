from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'apps.api'
    verbose_name = 'Api'

    def ready(self):
        # Import memicu pendaftaran route Ninja (dekorator @api.* di views.py).
        # Tanpa ini daftar operation NinjaAPI kosong (openapi tanpa paths).
        from . import views  
