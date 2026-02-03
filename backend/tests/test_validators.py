"""Tests for validation utilities."""

import pytest
from app.utils.validators import validate_nip, validate_pesel, format_nip, normalize_nip


class TestNipValidation:
    """Test NIP validation."""

    def test_valid_nip(self):
        """Test valid NIP numbers."""
        # These are example valid NIPs (checksum validated)
        valid_nips = [
            "5260251109",  # Example valid NIP
            "526-025-11-09",  # With dashes
            "526 025 11 09",  # With spaces
        ]

        for nip in valid_nips:
            assert validate_nip(nip) is True, f"NIP {nip} should be valid"

    def test_invalid_nip_length(self):
        """Test NIP with wrong length."""
        assert validate_nip("123456789") is False  # 9 digits
        assert validate_nip("12345678901") is False  # 11 digits

    def test_invalid_nip_checksum(self):
        """Test NIP with invalid checksum."""
        assert validate_nip("1234567890") is False
        assert validate_nip("0000000000") is False

    def test_invalid_nip_non_digits(self):
        """Test NIP with non-digit characters."""
        assert validate_nip("123456789a") is False
        assert validate_nip("abcdefghij") is False


class TestPeselValidation:
    """Test PESEL validation."""

    def test_valid_pesel(self):
        """Test valid PESEL numbers."""
        # Example valid PESEL
        valid_pesels = [
            "44051401458",
        ]

        for pesel in valid_pesels:
            assert validate_pesel(pesel) is True, f"PESEL {pesel} should be valid"

    def test_invalid_pesel_length(self):
        """Test PESEL with wrong length."""
        assert validate_pesel("1234567890") is False  # 10 digits
        assert validate_pesel("123456789012") is False  # 12 digits

    def test_invalid_pesel_checksum(self):
        """Test PESEL with invalid checksum."""
        assert validate_pesel("00000000000") is False


class TestNipFormatting:
    """Test NIP formatting."""

    def test_format_nip(self):
        """Test NIP formatting."""
        assert format_nip("5260251109") == "526-025-11-09"
        assert format_nip("5260251109", ".") == "526.025.11.09"

    def test_format_invalid_nip(self):
        """Test formatting invalid NIP returns original."""
        assert format_nip("123") == "123"

    def test_normalize_nip(self):
        """Test NIP normalization."""
        assert normalize_nip("526-025-11-09") == "5260251109"
        assert normalize_nip("526 025 11 09") == "5260251109"
        assert normalize_nip("5260251109") == "5260251109"
