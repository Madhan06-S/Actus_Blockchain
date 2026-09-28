"""API routes for contract hashing and integrity verification."""

from fastapi import APIRouter, status

from app.schemas.contract_hash import ContractHashResponse, HashVerificationResponse
from app.services.contract_hash_service import contract_hash_service

router = APIRouter(prefix="/api/v1/contracts", tags=["Contract Hashing & Integrity"])


@router.post(
    "/{contract_id}/hash",
    response_model=ContractHashResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate canonical SHA-256 integrity hash for a financial contract",
)
def generate_contract_hash(contract_id: str) -> ContractHashResponse:
    """Construct canonical representation and calculate SHA-256 fingerprint for a financial contract."""
    record = contract_hash_service.generate_contract_hash(contract_id)
    return ContractHashResponse.model_validate(record)


@router.get(
    "/{contract_id}/hash",
    response_model=ContractHashResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve previously generated SHA-256 integrity hash for a financial contract",
)
def get_contract_hash(contract_id: str) -> ContractHashResponse:
    """Retrieve the stored SHA-256 integrity hash digest and canonical payload for a contract ID."""
    record = contract_hash_service.get_contract_hash(contract_id)
    return ContractHashResponse.model_validate(record)


@router.post(
    "/{contract_id}/hash/verify",
    response_model=HashVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify integrity of stored financial contract hash against current state",
)
def verify_contract_hash(contract_id: str) -> HashVerificationResponse:
    """Recalculate SHA-256 hash from current canonical representation and compare against stored hash."""
    return contract_hash_service.verify_contract_hash(contract_id)
