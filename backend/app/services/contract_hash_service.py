"""Business service managing contract hashing, retrieval, and integrity verification."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status

from app.models.contract_hash import ContractHash, HashAlgorithm
from app.repositories.actus_repository import ActusRepository, actus_repository
from app.repositories.contract_hash_repository import ContractHashRepository, contract_hash_repository
from app.repositories.contract_repository import ContractRepository, contract_repository
from app.schemas.contract_hash import HashVerificationResponse
from app.services.contract_canonicalizer import ContractCanonicalizer
from app.services.contract_hasher import ContractHasher


class ContractHashService:
    """Service orchestrating contract canonicalization, cryptographic hashing, and integrity verification."""

    def __init__(
        self,
        hash_repo: ContractHashRepository = contract_hash_repository,
        contract_repo: ContractRepository = contract_repository,
        actus_repo: ActusRepository = actus_repository,
    ) -> None:
        self.hash_repository = hash_repo
        self.contract_repository = contract_repo
        self.actus_repository = actus_repo

    def generate_contract_hash(self, contract_id: str) -> ContractHash:
        """Fetch FinancialContract and ACTUS mapping, build canonical payload, calculate SHA-256 hash, and store."""
        domain_contract = self.contract_repository.get_by_id(contract_id)
        if not domain_contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Financial contract with ID '{contract_id}' not found.",
            )

        actus_record = self.actus_repository.get_by_source_id(contract_id)
        if not actus_record or not actus_record.actus_contract:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ACTUS mapping for contract ID '{contract_id}' not found. Please generate ACTUS mapping first.",
            )

        # Build canonical payload
        canonical_payload = ContractCanonicalizer.build_canonical_payload(
            financial_contract=domain_contract,
            actus_contract=actus_record.actus_contract,
        )

        # Calculate SHA-256 hash
        contract_hash_digest = ContractHasher.calculate_hash(canonical_payload)

        # Build domain record
        hash_record = ContractHash(
            contract_id=contract_id,
            hash_algorithm=HashAlgorithm.SHA256,
            canonical_payload_version=ContractCanonicalizer.VERSION,
            contract_hash=contract_hash_digest,
            canonical_payload=canonical_payload,
            created_at=datetime.now(timezone.utc),
        )

        # Save in repository
        saved_record = self.hash_repository.save(hash_record)
        return saved_record

    def get_contract_hash(self, contract_id: str) -> ContractHash:
        """Retrieve stored ContractHash for a contract ID."""
        record = self.hash_repository.get_by_contract_id(contract_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract hash for contract ID '{contract_id}' not found. Please generate hash first.",
            )
        return record

    def verify_contract_hash(self, contract_id: str) -> HashVerificationResponse:
        """Recalculate hash from current contract state and compare against stored hash."""
        stored_record = self.hash_repository.get_by_contract_id(contract_id)
        if not stored_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No stored contract hash found for contract ID '{contract_id}'. Please generate hash first.",
            )

        domain_contract = self.contract_repository.get_by_id(contract_id)
        if not domain_contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Financial contract with ID '{contract_id}' not found.",
            )

        actus_record = self.actus_repository.get_by_source_id(contract_id)
        actus_contract = actus_record.actus_contract if actus_record else None

        current_payload = ContractCanonicalizer.build_canonical_payload(
            financial_contract=domain_contract,
            actus_contract=actus_contract,
        )

        calculated_digest, matches = ContractHasher.verify_hash(
            canonical_payload=current_payload,
            expected_hash=stored_record.contract_hash,
        )

        return HashVerificationResponse(
            contract_id=contract_id,
            expected_hash=stored_record.contract_hash,
            calculated_hash=calculated_digest,
            matches=matches,
            hash_algorithm=HashAlgorithm(stored_record.hash_algorithm),
            canonical_payload_version=stored_record.canonical_payload_version,
        )


# Global default service instance
contract_hash_service = ContractHashService()
