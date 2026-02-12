"""
Unit tests for field-level encryption utilities.

Tests cover:
  - Encrypting and decrypting string values
  - Roundtrip encryption/decryption
  - Error handling (corrupted ciphertext)
  - Unicode and large text handling
"""

from __future__ import annotations


class TestEncryptDecrypt:
    """Tests for encrypt_value() and decrypt_value() functions."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypted data can be decrypted back to the original value."""
        from app.utils.encryption import decrypt_value, encrypt_value

        plaintext = "123-45-6789"  # SSN
        ciphertext = encrypt_value(plaintext)
        decrypted = decrypt_value(ciphertext)

        assert decrypted == plaintext

    def test_ciphertext_differs_from_plaintext(self):
        """The encrypted value must not equal the plaintext."""
        from app.utils.encryption import encrypt_value

        plaintext = "sensitive-data"
        ciphertext = encrypt_value(plaintext)

        assert ciphertext != plaintext
        assert ciphertext != ""

    def test_encrypt_produces_different_ciphertext_each_time(self):
        """Non-deterministic encryption yields different ciphertext per call."""
        from app.utils.encryption import encrypt_value

        plaintext = "same-value"
        ct1 = encrypt_value(plaintext)
        ct2 = encrypt_value(plaintext)

        # Fernet uses a random IV, so ciphertexts should differ
        assert ct1 != ct2

    def test_decrypt_corrupted_ciphertext_returns_empty(self):
        """Corrupted ciphertext returns empty string (graceful handling)."""
        from app.utils.encryption import decrypt_value

        # Implementation returns "" on failure, not raises
        result = decrypt_value("not-valid-ciphertext-at-all")
        assert result == ""

    def test_encrypt_empty_string_returns_empty(self):
        """Encrypting an empty string returns empty string."""
        from app.utils.encryption import decrypt_value, encrypt_value

        ciphertext = encrypt_value("")
        assert ciphertext == ""
        assert decrypt_value(ciphertext) == ""

    def test_decrypt_empty_string_returns_empty(self):
        """Decrypting an empty string returns empty string."""
        from app.utils.encryption import decrypt_value

        assert decrypt_value("") == ""

    def test_encrypt_unicode_characters(self):
        """Unicode text (names, addresses) encrypts and decrypts correctly."""
        from app.utils.encryption import decrypt_value, encrypt_value

        plaintext = "María García-López"
        ciphertext = encrypt_value(plaintext)
        decrypted = decrypt_value(ciphertext)
        assert decrypted == plaintext

    def test_encrypt_long_text(self):
        """Large text blocks (clinical notes) encrypt successfully."""
        from app.utils.encryption import decrypt_value, encrypt_value

        plaintext = "A" * 100_000  # 100KB clinical note
        ciphertext = encrypt_value(plaintext)
        decrypted = decrypt_value(ciphertext)
        assert decrypted == plaintext

    def test_encrypt_special_characters(self):
        """Special characters in text are preserved through encryption."""
        from app.utils.encryption import decrypt_value, encrypt_value

        plaintext = (
            'Patient: John Smith\nDOB: 1950-01-01\nNotes: "Critical" - see @doctor'
        )
        ciphertext = encrypt_value(plaintext)
        decrypted = decrypt_value(ciphertext)
        assert decrypted == plaintext

    def test_multiple_roundtrips(self):
        """Encrypting and decrypting multiple times works correctly."""
        from app.utils.encryption import decrypt_value, encrypt_value

        original = "sensitive-phi-data"

        # First roundtrip
        ct1 = encrypt_value(original)
        pt1 = decrypt_value(ct1)
        assert pt1 == original

        # Second roundtrip with the same plaintext
        ct2 = encrypt_value(pt1)
        pt2 = decrypt_value(ct2)
        assert pt2 == original

        # Ciphertexts should be different due to random IV
        assert ct1 != ct2
