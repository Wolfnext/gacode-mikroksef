"""Validation utilities for Polish identifiers."""

import re
from typing import Optional


def validate_nip(nip: str) -> bool:
    """
    Validate Polish NIP (tax identification number).

    NIP consists of 10 digits with checksum validation.
    """
    # Clean input
    nip = re.sub(r"[\s\-]", "", nip)

    if len(nip) != 10 or not nip.isdigit():
        return False
    if nip == "0" * 10:
        return False

    # NIP checksum weights
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]

    # Calculate checksum
    checksum = sum(int(nip[i]) * weights[i] for i in range(9))
    checksum = checksum % 11

    # Validate (checksum must equal last digit, and cannot be 10)
    return checksum == int(nip[9]) and checksum != 10


def validate_pesel(pesel: str) -> bool:
    """
    Validate Polish PESEL (personal identification number).

    PESEL consists of 11 digits with checksum validation.
    """
    # Clean input
    pesel = re.sub(r"[\s\-]", "", pesel)

    if len(pesel) != 11 or not pesel.isdigit():
        return False
    if pesel == "0" * 11:
        return False

    # PESEL checksum weights
    weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]

    # Calculate checksum
    checksum = sum(int(pesel[i]) * weights[i] for i in range(10))
    checksum = (10 - (checksum % 10)) % 10

    return checksum == int(pesel[10])


def format_nip(nip: str, separator: str = "-") -> str:
    """
    Format NIP with separators (XXX-XXX-XX-XX).

    Args:
        nip: Raw NIP string (10 digits)
        separator: Separator character

    Returns:
        Formatted NIP string
    """
    nip = re.sub(r"[\s\-]", "", nip)

    if len(nip) != 10:
        return nip

    return f"{nip[:3]}{separator}{nip[3:6]}{separator}{nip[6:8]}{separator}{nip[8:]}"


def normalize_nip(nip: str) -> str:
    """Remove all separators from NIP."""
    return re.sub(r"[\s\-]", "", nip)


def extract_nip_from_text(text: str) -> Optional[str]:
    """
    Extract NIP from text string.

    Args:
        text: Text that may contain NIP

    Returns:
        Extracted NIP or None
    """
    # Pattern for NIP (with or without separators)
    patterns = [
        r"\b(\d{3}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2})\b",  # XXX-XXX-XX-XX
        r"\b(\d{10})\b",  # XXXXXXXXXX
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            nip = normalize_nip(match.group(1))
            if validate_nip(nip):
                return nip

    return None
