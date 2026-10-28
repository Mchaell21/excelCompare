from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout

from .repository import UserRepository
from .otp_service import OTPTelegramService

class UserService:
    def __init__(self):
        self.repository = UserRepository()

    def login(self, request, username, password):
        user = self.repository.authenticate(request, username, password)
        if user is not None:
            auth_login(request, user)
        return user

    def logout(self, request):
        auth_logout(request)

    def list_users(self):
        return self.repository.list_users()

    def get_user(self, user_id):
        return self.repository.get_by_id(user_id)

    def get_user_by_username(self, username):
        return self.repository.get_by_username(username)

    def create_user(self, **kwargs):
        return self.repository.create_user(**kwargs)

    def set_role(self, user, role):
        return self.repository.set_role(user, role)

    def set_active(self, user, is_active):
        return self.repository.set_active(user, bool(is_active))

    def reset_password(self, user, raw_password):
        return self.repository.set_password(user, raw_password)

    def confirm_telegram(self, user) -> tuple[bool, str]:
        if not user.temporary_chat_tele_id:
            return False, "Tidak ada permintaan konfirmasi Telegram."

        user.chat_tele_id = user.temporary_chat_tele_id
        user.temporary_chat_tele_id = None
        user.save(update_fields=['chat_tele_id', 'temporary_chat_tele_id'])
        return True, "Akun Telegram berhasil dikonfirmasi dan terhubung!"

    def reject_telegram(self, user):
        user.temporary_chat_tele_id = None
        user.save(update_fields=['temporary_chat_tele_id'])

    def disconnect_telegram(self, user):
        user.chat_tele_id = None
        user.temporary_chat_tele_id = None
        user.save(update_fields=['chat_tele_id', 'temporary_chat_tele_id'])

    def list_has_connect_telegram_by_roles(self, roles: list[str]):
        return self.list_users().filter(
            chat_tele_id__isnull=False,
            groups__name__in=roles
        ).exclude(chat_tele_id='').distinct()

    def get_by_username(self, username: str):
        return self.repository.get_by_username(username)

    def verify_and_login_otp(self, request, user_id: int, otp_code: str):
        user = self.repository.get_by_id(user_id)
        if not user:
            return False, "User tidak ditemukan."

        if OTPTelegramService().verify_otp(user_id, otp_code):
            auth_login(request, user)
            return True, "Berhasil login."

        return False, "Kode OTP salah atau sudah kedaluwarsa."

user_service = UserService()
