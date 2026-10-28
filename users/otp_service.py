import random
from django.core.cache import cache

class OTPTelegramService:
    @staticmethod
    def generate_otp(user_id) -> str:
        otp = f"{random.randint(100000, 999999)}"
        cache_key = f"otp_user_{str(user_id)}"
        cache.set(cache_key, otp, timeout=300)
        return otp

    @staticmethod
    def verify_otp(user_id, input_otp: str) -> bool:
        cache_key = f"otp_user_{str(user_id)}"
        saved_otp = cache.get(cache_key)
        if saved_otp and str(saved_otp) == str(input_otp):
            cache.delete(cache_key)
            return True
        return False
