# backend/app/utils/encryption.py

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..config import settings

# Function to generate key from secret key
def _get_encryption_key():
    """Generate encryption key from app secret key."""
    if not settings.SECRET_KEY:
        raise ValueError("SECRET_KEY not set in configuration")
        
    # Use key derivation to get a proper length key for Fernet
    salt = os.environ.get("ENCRYPTION_SALT", "skipper_default_salt").encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
    return key

# Encryption functions
def encrypt_value(value):
    """Encrypt a string value."""
    if value is None:
        return None
        
    if not isinstance(value, str):
        value = str(value)
        
    key = _get_encryption_key()
    cipher = Fernet(key)
    encrypted_value = cipher.encrypt(value.encode())
    return encrypted_value.decode()
    
def decrypt_value(encrypted_value):
    """Decrypt an encrypted value."""
    if encrypted_value is None:
        return None
    
    key = _get_encryption_key()
    cipher = Fernet(key)
    decrypted_value = cipher.decrypt(encrypted_value.encode())
    return decrypted_value.decode()