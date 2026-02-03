"""Tests for cryptography service."""

import pytest
import base64
from app.services.crypto_service import CryptoService


class TestCryptoService:
    """Test cryptography service."""

    @pytest.fixture
    def crypto_service(self):
        """Create crypto service instance."""
        return CryptoService()

    def test_generate_aes_key(self, crypto_service):
        """Test AES key generation."""
        key = crypto_service.generate_aes_key()

        assert len(key) == 32  # 256 bits
        assert isinstance(key, bytes)

    def test_generate_iv(self, crypto_service):
        """Test IV generation."""
        iv = crypto_service.generate_iv()

        assert len(iv) == 16  # 128 bits
        assert isinstance(iv, bytes)

    def test_aes_encrypt_decrypt(self, crypto_service):
        """Test AES encryption and decryption."""
        key = crypto_service.generate_aes_key()
        iv = crypto_service.generate_iv()
        plaintext = b"Test message for encryption"

        # Encrypt
        encrypted = crypto_service.encrypt_with_aes(plaintext, key, iv)

        assert encrypted != plaintext
        assert len(encrypted) > 0

        # Decrypt
        decrypted = crypto_service.decrypt_with_aes(encrypted, key, iv)

        assert decrypted == plaintext

    def test_aes_padding(self, crypto_service):
        """Test PKCS#7 padding."""
        key = crypto_service.generate_aes_key()
        iv = crypto_service.generate_iv()

        # Test various message lengths
        for length in [1, 15, 16, 17, 31, 32, 33]:
            plaintext = b"x" * length
            encrypted = crypto_service.encrypt_with_aes(plaintext, key, iv)
            decrypted = crypto_service.decrypt_with_aes(encrypted, key, iv)
            assert decrypted == plaintext

    def test_compute_sha256(self, crypto_service):
        """Test SHA-256 hash computation."""
        data = b"Test data for hashing"

        hash_value = crypto_service.compute_sha256(data)

        # Should be base64 encoded
        assert isinstance(hash_value, str)
        # Can decode from base64
        decoded = base64.b64decode(hash_value)
        assert len(decoded) == 32  # SHA-256 produces 32 bytes

    def test_compute_sha256_hex(self, crypto_service):
        """Test SHA-256 hex hash."""
        data = b"Test data"

        hash_value = crypto_service.compute_sha256_hex(data)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # 32 bytes = 64 hex chars

    def test_verify_hash(self, crypto_service):
        """Test hash verification."""
        data = b"Test data"
        expected_hash = crypto_service.compute_sha256(data)

        assert crypto_service.verify_hash(data, expected_hash, "base64") is True
        assert crypto_service.verify_hash(data, "wrong-hash", "base64") is False

    def test_has_public_key_initially_false(self, crypto_service):
        """Test that public key is not loaded initially."""
        assert crypto_service.has_public_key is False

    def test_encrypt_without_public_key_raises(self, crypto_service):
        """Test that encryption fails without public key."""
        with pytest.raises(ValueError, match="Ministry public key not loaded"):
            crypto_service.encrypt_for_ksef(b"test data")

    def test_encrypt_token_without_public_key_raises(self, crypto_service):
        """Test that token encryption fails without public key."""
        with pytest.raises(ValueError):
            crypto_service.encrypt_token("test-token")


class TestCryptoServiceWithKey:
    """Test crypto service with mock public key."""

    @pytest.fixture
    def crypto_with_key(self):
        """Create crypto service with a test RSA key."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization

        # Generate test key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )

        public_key = private_key.public_key()

        # Export public key as PEM
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        service = CryptoService()
        service.set_ministry_public_key(pem)

        return service, private_key

    def test_has_public_key_after_loading(self, crypto_with_key):
        """Test that public key is loaded."""
        service, _ = crypto_with_key
        assert service.has_public_key is True

    def test_encrypt_for_ksef(self, crypto_with_key):
        """Test full KSeF encryption."""
        service, _ = crypto_with_key
        plaintext = b"Test invoice data"

        encrypted = service.encrypt_for_ksef(plaintext)

        assert isinstance(encrypted, bytes)
        assert len(encrypted) > len(plaintext)

        # Check package structure
        key_length = int.from_bytes(encrypted[:2], byteorder='big')
        assert key_length > 0
        assert len(encrypted) > 2 + key_length + 16  # key_len + encrypted_key + iv + data

    def test_encrypt_token(self, crypto_with_key):
        """Test token encryption."""
        service, _ = crypto_with_key
        token = "test-authorization-token"

        encrypted = service.encrypt_token(token)

        assert isinstance(encrypted, str)
        # Should be valid base64
        decoded = base64.b64decode(encrypted)
        assert len(decoded) > 0
