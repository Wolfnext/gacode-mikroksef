"""
Cryptography Service
Handles encryption/decryption for KSeF communication.
"""

import base64
import hashlib
import logging
import os
from typing import Optional, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.x509 import load_pem_x509_certificate, load_der_x509_certificate

logger = logging.getLogger(__name__)


class CryptoService:
    """Service for cryptographic operations required by KSeF."""

    def __init__(self) -> None:
        self._ministry_public_key: Optional[rsa.RSAPublicKey] = None
        self._ministry_public_key_pem: Optional[str] = None

    def set_ministry_public_key(self, pem_data: str) -> None:
        """
        Load Ministry's public key from PEM-encoded certificate or key.

        Args:
            pem_data: PEM-encoded certificate or public key
        """
        try:
            # Try loading as certificate first
            if "BEGIN CERTIFICATE" in pem_data:
                cert = load_pem_x509_certificate(
                    pem_data.encode(), default_backend()
                )
                self._ministry_public_key = cert.public_key()
            else:
                # Load as raw public key
                self._ministry_public_key = serialization.load_pem_public_key(
                    pem_data.encode(), default_backend()
                )
            self._ministry_public_key_pem = pem_data
            logger.info("Ministry public key loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load public key: {e}")
            raise ValueError(f"Invalid public key format: {e}")

    def set_ministry_public_key_from_der(self, base64_der: str) -> None:
        """
        Load Ministry's public key from base64-encoded DER certificate.

        Args:
            base64_der: Base64-encoded DER certificate (from KSeF v2 API)
        """
        try:
            der_bytes = base64.b64decode(base64_der)
            cert = load_der_x509_certificate(der_bytes, default_backend())
            self._ministry_public_key = cert.public_key()
            # Convert to PEM for storage
            self._ministry_public_key_pem = cert.public_bytes(
                serialization.Encoding.PEM
            ).decode("utf-8")
            logger.info("Ministry public key loaded from DER certificate")
        except Exception as e:
            logger.error(f"Failed to load DER certificate: {e}")
            raise ValueError(f"Invalid DER certificate: {e}")

    @property
    def has_public_key(self) -> bool:
        """Check if Ministry public key is loaded."""
        return self._ministry_public_key is not None

    def generate_aes_key(self) -> bytes:
        """Generate random 256-bit AES key."""
        return os.urandom(32)

    def generate_iv(self) -> bytes:
        """Generate random 128-bit IV for AES-CBC."""
        return os.urandom(16)

    def _pkcs7_pad(self, data: bytes, block_size: int = 16) -> bytes:
        """Apply PKCS#7 padding."""
        padding_length = block_size - (len(data) % block_size)
        return data + bytes([padding_length] * padding_length)

    def _pkcs7_unpad(self, data: bytes) -> bytes:
        """Remove PKCS#7 padding."""
        padding_length = data[-1]
        if padding_length > 16 or padding_length == 0:
            raise ValueError("Invalid PKCS#7 padding")
        return data[:-padding_length]

    def encrypt_with_aes(self, data: bytes, key: bytes, iv: bytes) -> bytes:
        """
        Encrypt data using AES-256-CBC.

        Args:
            data: Plaintext data to encrypt
            key: 256-bit AES key
            iv: 128-bit initialization vector

        Returns:
            Encrypted data
        """
        padded_data = self._pkcs7_pad(data)

        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend(),
        )
        encryptor = cipher.encryptor()
        return encryptor.update(padded_data) + encryptor.finalize()

    def decrypt_with_aes(self, encrypted_data: bytes, key: bytes, iv: bytes) -> bytes:
        """
        Decrypt data using AES-256-CBC.

        Args:
            encrypted_data: Ciphertext to decrypt
            key: 256-bit AES key
            iv: 128-bit initialization vector

        Returns:
            Decrypted plaintext data
        """
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend(),
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        return self._pkcs7_unpad(padded_data)

    def encrypt_key_with_rsa(self, aes_key: bytes) -> bytes:
        """
        Encrypt AES key using Ministry's RSA public key (RSA-OAEP).

        Args:
            aes_key: AES key to encrypt

        Returns:
            RSA-encrypted key
        """
        if not self._ministry_public_key:
            raise ValueError("Ministry public key not loaded")

        return self._ministry_public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    def encrypt_for_ksef(self, data: bytes) -> bytes:
        """
        Encrypt data for KSeF transmission.

        Package format:
        [2 bytes: RSA-encrypted key length]
        [N bytes: RSA-encrypted AES key]
        [16 bytes: IV]
        [M bytes: AES-encrypted data]

        Args:
            data: Plaintext data to encrypt

        Returns:
            Encrypted package ready for KSeF
        """
        if not self._ministry_public_key:
            raise ValueError("Ministry public key not loaded")

        # Generate encryption materials
        aes_key = self.generate_aes_key()
        iv = self.generate_iv()

        # Encrypt data with AES
        encrypted_data = self.encrypt_with_aes(data, aes_key, iv)

        # Encrypt AES key with RSA
        encrypted_key = self.encrypt_key_with_rsa(aes_key)

        # Build package
        key_length = len(encrypted_key).to_bytes(2, byteorder="big")
        package = key_length + encrypted_key + iv + encrypted_data

        logger.debug(
            f"Encrypted package: key_len={len(encrypted_key)}, "
            f"iv_len=16, data_len={len(encrypted_data)}"
        )

        return package

    def encrypt_invoice(self, invoice_xml: bytes) -> bytes:
        """
        Encrypt invoice XML for KSeF submission.

        Args:
            invoice_xml: Invoice XML content

        Returns:
            Encrypted invoice package
        """
        return self.encrypt_for_ksef(invoice_xml)

    def encrypt_token(self, token: str) -> str:
        """
        Encrypt authorization token for session initialization (v1 API).

        Args:
            token: Authorization token string

        Returns:
            Base64-encoded encrypted token package
        """
        encrypted_package = self.encrypt_for_ksef(token.encode("utf-8"))
        return base64.b64encode(encrypted_package).decode("utf-8")

    def encrypt_token_v2(self, token_with_timestamp: str) -> str:
        """
        Encrypt token|timestamp for v2 API session initialization.

        v2 API requires RSA-OAEP with SHA-256 encryption of "token|timestampMs".
        No AES layer - direct RSA encryption of the token string.

        Args:
            token_with_timestamp: String in format "token|timestampMs"

        Returns:
            Base64-encoded RSA-OAEP encrypted string
        """
        if not self._ministry_public_key:
            raise ValueError("Ministry public key not loaded")

        # Encrypt directly with RSA-OAEP SHA-256
        encrypted = self._ministry_public_key.encrypt(
            token_with_timestamp.encode("utf-8"),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

        return base64.b64encode(encrypted).decode("utf-8")

    def compute_sha256(self, data: bytes) -> str:
        """
        Compute SHA-256 hash and return Base64-encoded.

        Args:
            data: Data to hash

        Returns:
            Base64-encoded SHA-256 hash
        """
        hash_bytes = hashlib.sha256(data).digest()
        return base64.b64encode(hash_bytes).decode("utf-8")

    def compute_sha256_hex(self, data: bytes) -> str:
        """
        Compute SHA-256 hash and return hex-encoded.

        Args:
            data: Data to hash

        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(data).hexdigest()

    def verify_hash(self, data: bytes, expected_hash: str, encoding: str = "base64") -> bool:
        """
        Verify SHA-256 hash of data.

        Args:
            data: Data to verify
            expected_hash: Expected hash value
            encoding: Hash encoding ('base64' or 'hex')

        Returns:
            True if hash matches
        """
        if encoding == "base64":
            computed = self.compute_sha256(data)
        else:
            computed = self.compute_sha256_hex(data)

        return computed == expected_hash


# Singleton instance
crypto_service = CryptoService()
