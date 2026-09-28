"""Conversion and normalization utilities for SHA-256 <-> bytes32 and Decimal <-> Contract Units."""

from decimal import Decimal
from typing import Union

from app.blockchain.exceptions import InvalidActusHashError


def sha256_to_bytes32(sha256_hex: str) -> bytes:
    """Convert a 64-character hexadecimal SHA-256 digest string to 32 bytes.
    
    Accepts raw 64-char hex or '0x'-prefixed 66-char hex strings.
    """
    clean_hex = sha256_hex.strip()
    if clean_hex.startswith("0x") or clean_hex.startswith("0X"):
        clean_hex = clean_hex[2:]

    if len(clean_hex) != 64:
        raise InvalidActusHashError(
            f"SHA-256 hash must be exactly 64 hexadecimal characters, got {len(clean_hex)} chars."
        )

    try:
        return bytes.fromhex(clean_hex)
    except ValueError as exc:
        raise InvalidActusHashError(f"Invalid hexadecimal string for SHA-256 hash: {str(exc)}") from exc


def bytes32_to_sha256(b32_val: Union[bytes, str]) -> str:
    """Convert a 32-byte value (bytes or '0x'-prefixed hex string) to a 64-char lowercase SHA-256 hex string."""
    if isinstance(b32_val, bytes):
        if len(b32_val) != 32:
            raise InvalidActusHashError(f"Expected 32 bytes for bytes32, got {len(b32_val)} bytes.")
        return b32_val.hex().lower()

    if isinstance(b32_val, str):
        clean_hex = b32_val.strip()
        if clean_hex.startswith("0x") or clean_hex.startswith("0X"):
            clean_hex = clean_hex[2:]
        if len(clean_hex) != 64:
            raise InvalidActusHashError(f"Expected 64 hex characters for bytes32, got {len(clean_hex)} chars.")
        try:
            # Verify valid hex
            bytes.fromhex(clean_hex)
            return clean_hex.lower()
        except ValueError as exc:
            raise InvalidActusHashError(f"Invalid hexadecimal bytes32 string: {str(exc)}") from exc

    raise InvalidActusHashError(f"Unsupported bytes32 value type: {type(b32_val)}")


def decimal_to_contract_units(amount: Decimal) -> int:
    """Convert Decimal monetary amount to integer contract accounting units (₹1.00 = 1 unit).
    
    In Phase 7, 1 INR = 1 blockchain unit. Raises ValueError if non-zero fractional cents exist.
    """
    # Round to 2 decimal places first
    quantized = amount.quantize(Decimal("0.01"))
    # Check if there is a non-zero fractional part
    if quantized % Decimal("1") != Decimal("0"):
        raise ValueError(
            f"Monetary amount {amount} has a fractional unit remainder ({quantized}) which cannot be represented as an exact integer contract unit in Phase 7."
        )
    return int(quantized)


def contract_units_to_decimal(units: int) -> Decimal:
    """Convert integer contract accounting units to backend Decimal monetary representation."""
    return Decimal(str(units)).quantize(Decimal("0.01"))
