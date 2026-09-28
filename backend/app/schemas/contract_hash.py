"""Pydantic request and response schemas for contract hashing and verification API endpoints."""

from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict, Field

from app.models.contract_hash import HashAlgorithm


class ContractHashResponse(BaseModel):
    """Response schema for contract hash generation and retrieval."""

    contract_id: str = Field(..., description="Unique source FinancialContract ID")
    hash_algorithm: HashAlgorithm = Field(..., description="Hashing algorithm used")
    canonical_payload_version: str = Field(..., description="Canonical payload schema version")
    contract_hash: str = Field(
        ..., description="64-character lowercase SHA-256 hexadecimal hash digest"
    )
    canonical_payload: Dict[str, Any] = Field(
        ..., description="Deterministic canonical JSON payload that was hashed"
    )
    created_at: datetime = Field(..., description="UTC creation timestamp")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class HashVerificationResponse(BaseModel):
    """Response schema for contract hash integrity verification."""

    contract_id: str = Field(..., description="Unique source FinancialContract ID")
    expected_hash: str = Field(
        ..., description="Stored / previously generated contract hash digest"
    )
    calculated_hash: str = Field(
        ..., description="Newly calculated contract hash digest from current state"
    )
    matches: bool = Field(
        ..., description="Boolean indicating whether recalculated hash matches stored hash"
    )
    hash_algorithm: HashAlgorithm = Field(..., description="Hashing algorithm used")
    canonical_payload_version: str = Field(..., description="Canonical payload schema version")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
