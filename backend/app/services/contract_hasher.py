"""Contract Hasher Service computing deterministic SHA-256 cryptographic digests."""

import hashlib
from typing import Any, Dict, Tuple

from app.models.contract_hash import HashAlgorithm
from app.services.contract_canonicalizer import ContractCanonicalizer


class ContractHasher:
    """Cryptographic hashing service generating SHA-256 integrity fingerprints."""

    ALGORITHM = HashAlgorithm.SHA256

    @classmethod
    def calculate_hash(cls, canonical_payload: Dict[str, Any]) -> str:
        """Calculate a 64-character lowercase SHA-256 hexadecimal hash from canonical payload."""
        payload_bytes = ContractCanonicalizer.to_canonical_bytes(canonical_payload)
        digest = hashlib.sha256(payload_bytes).hexdigest()
        return digest.lower()

    @classmethod
    def verify_hash(
        cls, canonical_payload: Dict[str, Any], expected_hash: str
    ) -> Tuple[str, bool]:
        """Recalculate hash for canonical payload and verify if it matches expected stored hash.
        
        Returns a tuple of (calculated_hash, matches_boolean).
        """
        calculated_hash = cls.calculate_hash(canonical_payload)
        matches = calculated_hash == expected_hash.strip().lower()
        return calculated_hash, matches
