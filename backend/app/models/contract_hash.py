"""Domain model definitions for contract hashing and integrity verification."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict, Field


class HashAlgorithm(str, Enum):
    """Supported cryptographic hash algorithms."""

    SHA256 = "SHA-256"


class ContractHash(BaseModel):
    """Domain model representing a generated contract integrity hash record."""

    contract_id: str = Field(..., description="Unique source FinancialContract ID")
    hash_algorithm: HashAlgorithm = Field(
        default=HashAlgorithm.SHA256, description="Cryptographic hashing algorithm used"
    )
    canonical_payload_version: str = Field(
        default="v1", description="Version of canonical serialization schema"
    )
    contract_hash: str = Field(
        ..., description="64-character lowercase SHA-256 hexadecimal hash digest"
    )
    canonical_payload: Dict[str, Any] = Field(
        ..., description="Deterministic canonical JSON payload that was hashed"
    )
    created_at: datetime = Field(..., description="UTC creation timestamp of this hash record")

    model_config = ConfigDict(
        use_enum_values=True,
        arbitrary_types_allowed=True,
    )
