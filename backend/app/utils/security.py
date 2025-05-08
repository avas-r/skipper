"""
Security utility module.

This module provides security utilities for encryption, decryption,
and other security-related functions.
"""

import os
import base64
import secrets
import uuid
from typing import Optional, Dict, Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..config import settings

# Global Fernet instance for encryption/decryption
_fernet = None

def get_fernet():
    """
    Get the Fernet instance for encryption/decryption.
    
    Returns:
        Fernet: Fernet instance
    """
    global _fernet
    if _fernet is None:
        # Use SECRET_KEY from settings to derive encryption key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"orchestrator-salt",  # In production, use a secure random salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
        _fernet = Fernet(key)
    return _fernet

def encrypt_value(value: str) -> str:
    """
    Encrypt a value using Fernet symmetric encryption.
    
    Args:
        value: Value to encrypt
        
    Returns:
        str: Encrypted value as base64 string
    """
    if not value:
        return None
        
    fernet = get_fernet()
    encrypted = fernet.encrypt(value.encode())
    return encrypted.decode()

def decrypt_value(encrypted_value: str) -> Optional[str]:
    """
    Decrypt a value using Fernet symmetric encryption.
    
    Args:
        encrypted_value: Encrypted value as base64 string
        
    Returns:
        Optional[str]: Decrypted value or None if decryption fails
    """
    if not encrypted_value:
        return None
        
    try:
        fernet = get_fernet()
        decrypted = fernet.decrypt(encrypted_value.encode())
        return decrypted.decode()
    except Exception as e:
        return None

def generate_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        str: Secure API key
    """
    # Generate a random token with 32 bytes of randomness
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage.
    
    Args:
        api_key: API key to hash
        
    Returns:
        str: Hashed API key
    """
    # Use a secure hash function (SHA-256) to hash the API key
    digest = hashes.Hash(hashes.SHA256())
    digest.update(api_key.encode())
    return base64.b64encode(digest.finalize()).decode()

def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against a hashed key.
    
    Args:
        api_key: API key to verify
        hashed_key: Hashed API key to compare against
        
    Returns:
        bool: True if API key is valid, False otherwise
    """
    return hash_api_key(api_key) == hashed_key

def generate_random_password(length: int = 12) -> str:
    """
    Generate a random password.
    
    Args:
        length: Password length
        
    Returns:
        str: Random password
    """
    import string
    # Include at least one of each character type
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits + "!@#$%^&*()-_=+"
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*()-_=+"),
    ]
    # Fill the rest of the password with random characters
    password.extend(secrets.choice(chars) for _ in range(length - 4))
    # Shuffle the password to randomize the position of the required character types
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)

def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mask sensitive data in a dictionary.
    
    Args:
        data: Dictionary containing sensitive data
        
    Returns:
        Dict[str, Any]: Dictionary with sensitive data masked
    """
    sensitive_keys = [
        "password", "secret", "key", "token", "credential",
        "api_key", "auth", "access_token", "refresh_token"
    ]
    
    result = {}
    
    # Recursive function to mask sensitive values
    def mask_dict(d, path=""):
        if isinstance(d, dict):
            return {k: mask_dict(v, f"{path}.{k}" if path else k) for k, v in d.items()}
        elif isinstance(d, list):
            return [mask_dict(item, path) for item in d]
        else:
            # Check if current path contains a sensitive key
            if any(key in path.lower() for key in sensitive_keys):
                if isinstance(d, str) and d:
                    return "***" + d[-4:] if len(d) > 4 else "****"
                return "****"
            return d
    
    return mask_dict(data)