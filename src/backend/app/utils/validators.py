"""
Healthcare-specific validators for common coded identifiers.
"""

from __future__ import annotations

import re


def validate_npi(npi: str) -> bool:
    """Validate a National Provider Identifier (NPI).

    NPIs are 10-digit numbers that satisfy the Luhn check-digit algorithm
    with the constant prefix ``80840`` prepended (as defined by CMS).
    """
    if not npi or not re.fullmatch(r"\d{10}", npi):
        return False

    # Luhn algorithm with the 80840 prefix
    digits = [int(d) for d in "80840" + npi]
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def validate_mrn(mrn: str) -> bool:
    """Validate a Medical Record Number.

    MRNs are facility-specific.  This validator accepts alphanumeric
    strings between 4 and 20 characters.
    """
    if not mrn:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9\-]{4,20}", mrn))


def validate_icd10(code: str) -> bool:
    """Validate an ICD-10-CM code format.

    Format: a letter followed by 2 digits, optionally a dot and 1-4
    alphanumeric characters (e.g. ``A00``, ``A00.0``, ``S72.001A``).
    """
    if not code:
        return False
    return bool(re.fullmatch(r"[A-Za-z]\d{2}(\.\d{1,4}[A-Za-z]?)?", code))


def validate_loinc(code: str) -> bool:
    """Validate a LOINC code format.

    LOINC codes consist of 1-5 digits, a hyphen, and a single check digit
    (e.g. ``2160-0``, ``85354-9``).
    """
    if not code:
        return False
    return bool(re.fullmatch(r"\d{1,5}-\d", code))


def validate_snomed(code: str) -> bool:
    """Validate a SNOMED CT concept identifier (6-18 digit number)."""
    if not code:
        return False
    return bool(re.fullmatch(r"\d{6,18}", code))


def validate_phone(phone: str) -> bool:
    """Basic US phone number validation."""
    if not phone:
        return False
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone)
    return bool(re.fullmatch(r"\+?1?\d{10}", cleaned))


def validate_ssn(ssn: str) -> bool:
    """Validate SSN format (XXX-XX-XXXX)."""
    if not ssn:
        return False
    return bool(re.fullmatch(r"\d{3}-\d{2}-\d{4}", ssn))
