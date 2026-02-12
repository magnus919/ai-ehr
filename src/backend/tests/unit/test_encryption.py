"""
Unit tests for field-level encryption utilities.

Tests cover:
  - Encrypting and decrypting string values
  - Encrypting structured data (dicts)
  - Key rotation
  - Error handling (wrong key, corrupted ciphertext)
  - Deterministic vs non-deterministic modes
"""

from __future__ import annotations

import base64
import os

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_fernet_key() -> str:
    """Generate a valid Fernet-compatible key for testing."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


class TestFieldEncryption:
    """Tests for the FieldEncryption utility class."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypted data can be decrypted back to the original value."""
        from app.utils.encryption import FieldEncryption

        key = _generate_fernet_key()
        enc = FieldEncryption(key)

        plaintext = "123-45-6789"  # SSN
        ciphertext = enc.encrypt(plaintext)
        decrypted = enc.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_ciphertext_differs_from_plaintext(self):
        """The encrypted value must not equal the plaintext."""
        from app.utils.encryption import FieldEncryption

        key = _generate_fernet_key()
        enc = FieldEncryption(key)

        plaintext = "sensitive-data"
        ciphertext = enc.encrypt(plaintext)

        assert ciphertext != plaintext

    def test_encrypt_produces_different_ciphertext_each_time(self):
        """Non-deterministic encryption yields different ciphertext per call."""
        from app.utils.encryption import FieldEncryption

        key = _generate_fernet_key()
        enc = FieldEncryption(key)

        plaintext = "same-value"
        ct1 = enc.encrypt(plaintext)
        ct2 = enc.encrypt(plaintext)

        # Fernet uses a random IV, so ciphertexts should differ
        assert ct1 != ct2

    def test_decrypt_with_wrong_key_raises(self):
        """Decrypting with a different key raises an error."""
        from app.utils.encryption import FieldEncryption

        key1 = _generate_fernet_key()
        key2 = _generate_fernet_key()

        enc1 = FieldEncryption(key1)
        enc2 = FieldEncryption(key2)

        ciphertext = enc1.encrypt("secret-value")

        with pytest.raises(Exception):  # InvalidToken
            enc2.decrypt(ciphertext)

    def test_decrypt_corrupted_ciphertext_raises(self):
        """Corrupted ciphertext raises an error during decryption."""
        from app.utils.encryption import FieldEncryption

        key = _generate_fernet_key()
        enc = FieldEncryption(key)

        with pytest.raises(Exception):
            enc.decrypt("not-valid-ciphertext-at-all")

    def test_encrypt_empty_string(self):
        """Encrypting an empty string works correctly."""
        from app.utils.encryption import FieldEncryption

        key = _generate_fernet_key()
        enc = FieldEncryption(key)

        ciphertext = enc.encrypt("")
        assert enc.decrypt(ciphertext) == ""

    def test_encrypt_unicode_characters(self):
        """Unicode text (names, addresses) encrypts and decrypts correctly."""
        from app.utils.encryption import FieldEncryption

        key = _generate_fernet_key()
        enc = FieldEncryption(key)

        plaintext = "Maria Garcia-Lopez"
        ciphertext = enc.encrypt(plaintext)
        assert enc.decrypt(ciphertext) == plaintext

    def test_encrypt_long_text(self):
        """Large text blocks (clinical notes) encrypt successfully."""
        from app.utils.encryption import FieldEncryption

        key = _generate_fernet_key()
        enc = FieldEncryption(key)

        plaintext = "A" * 100_000  # 100KB clinical note
        ciphertext = enc.encrypt(plaintext)
        assert enc.decrypt(ciphertext) == plaintext


class TestFieldEncryptionDict:
    """Tests for encrypting structured data (dictionaries)."""

    def test_encrypt_dict_fields(self):
        """Specific fields in a dict are encrypted while others remain clear."""
        from app.utils.encryption import FieldEncryption

        key = _generate_fernet_key()
        enc = FieldEncryption(key)

        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "ssn": "123-45-6789",
            "date_of_birth": "1985-06-15",
            "mrn": "MRN-12345",
        }
        phi_fields = ["ssn", "first_name", "last_name"]

        encrypted = enc.encrypt_fields(data, phi_fields)

        # PHI fields are encrypted
        assert encrypted["ssn"] != "123-45-6789"
        assert encrypted["first_name"] != "Jane"
        assert encrypted["last_name"] != "Doe"

        # Non-PHI fields remain in the clear
        assert encrypted["mrn"] == "MRN-12345"
        assert encrypted["date_of_birth"] == "1985-06-15"

    def test_decrypt_dict_fields(self):
        """Encrypted dict fields can be decrypted back to original values."""
        from app.utils.encryption import FieldEncryption

        key = _generate_fernet_key()
        enc = FieldEncryption(key)

        data = {"ssn": "123-45-6789", "name": "Jane Doe"}
        phi_fields = ["ssn", "name"]

        encrypted = enc.encrypt_fields(data, phi_fields)
        decrypted = enc.decrypt_fields(encrypted, phi_fields)

        assert decrypted["ssn"] == "123-45-6789"
        assert decrypted["name"] == "Jane Doe"


class TestKeyRotation:
    """Tests for encryption key rotation."""

    def test_rotate_key_re_encrypts_data(self):
        """Key rotation decrypts with old key and re-encrypts with new key."""
        from app.utils.encryption import FieldEncryption

        old_key = _generate_fernet_key()
        new_key = _generate_fernet_key()

        old_enc = FieldEncryption(old_key)
        new_enc = FieldEncryption(new_key)

        plaintext = "SSN: 123-45-6789"
        old_ciphertext = old_enc.encrypt(plaintext)

        # Rotate: decrypt with old key, encrypt with new key
        rotated_ciphertext = FieldEncryption.rotate(old_ciphertext, old_key, new_key)

        # Old key cannot decrypt the rotated ciphertext
        with pytest.raises(Exception):
            old_enc.decrypt(rotated_ciphertext)

        # New key can decrypt
        assert new_enc.decrypt(rotated_ciphertext) == plaintext

    def test_rotate_preserves_original_value(self):
        """The plaintext is identical before and after key rotation."""
        from app.utils.encryption import FieldEncryption

        old_key = _generate_fernet_key()
        new_key = _generate_fernet_key()

        old_enc = FieldEncryption(old_key)
        new_enc = FieldEncryption(new_key)

        original = "Patient: John Smith, DOB: 1950-01-01"
        ciphertext = old_enc.encrypt(original)
        rotated = FieldEncryption.rotate(ciphertext, old_key, new_key)

        assert new_enc.decrypt(rotated) == original
