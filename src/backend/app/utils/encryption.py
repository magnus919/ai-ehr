"""
Field-level encryption for sensitive PHI data (SSN, etc.).

Uses Fernet symmetric encryption (AES-128-CBC under the hood via the
``cryptography`` library).  In production the FIELD_ENCRYPTION_KEY must be
a valid Fernet key stored securely (e.g. via a secrets manager).
"""

from __future__ import annotations

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    global _fernet  # noqa: WPS420
    if _fernet is not None:
        return _fernet

    key = settings.FIELD_ENCRYPTION_KEY
    if not key:
        # In development/test, generate an ephemeral key.  This means
        # encrypted data will NOT survive process restarts.
        key = Fernet.generate_key().decode()

    # Accept raw 32-byte keys (url-safe-b64-encoded to 44 chars) as well
    # as full Fernet keys.
    if len(key) == 44:
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    else:
        # Derive a valid Fernet key from the provided secret
        padded = base64.urlsafe_b64encode(key.encode()[:32].ljust(32, b"\0"))
        _fernet = Fernet(padded)
    return _fernet


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value and return the ciphertext as a UTF-8 string."""
    if not plaintext:
        return ""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a ciphertext string.  Returns empty string on failure."""
    if not ciphertext:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(ciphertext.encode()).decode()
    except (InvalidToken, Exception):
        return ""
