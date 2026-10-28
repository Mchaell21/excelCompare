import json
import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from django.conf import settings

def decrypt_payload(encrypted_b64_string):
    private_key = getattr(settings, 'PRIVATE_KEY_AUTH')
    encrypted_bytes = base64.b64decode(encrypted_b64_string)

    decrypted_bytes = private_key.decrypt(
        encrypted_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return json.loads(decrypted_bytes.decode('utf-8'))

def encrypt_payload(data_dict):
    public_key = getattr(settings, 'PUBLIC_KEY_AUTH')
    json_bytes = json.dumps(data_dict).encode('utf-8')
    
    encrypted_bytes = public_key.encrypt(
        json_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return base64.b64encode(encrypted_bytes).decode('utf-8')