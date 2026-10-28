import os
from django.conf import settings
from cryptography.hazmat.primitives import serialization

def load_private_key_from_env(env_var_name="PRIVATE_KEY_AUTH"):
    private_key_str = os.getenv(env_var_name)
    if not private_key_str:
        raise ValueError(f"Environment variable {env_var_name} tidak ditemukan.")
    
    formatted_key = private_key_str.replace('\\n', '\n')
    return serialization.load_pem_private_key(
        formatted_key.encode('utf-8'),
        password=None
    )

def load_public_key_from_string(public_key_pem_str):
    formatted_key = public_key_pem_str.replace('\\n', '\n')
    return serialization.load_pem_public_key(
        formatted_key.encode('utf-8')
    )