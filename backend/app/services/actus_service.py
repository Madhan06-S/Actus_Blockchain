"""Service layer for managing ACTUS contract mappings."""

from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status

from app.repositories.actus_repository import ActusRepository, actus_repository
from app.schemas.actus import ActusContractResponse, ActusMappingResponse
from app.services.actus_mapper import ActusMapper
from app.services.contract_service import ContractService, contract_service


class ActusService:
    """Business service for creating and retrieving ACTUS contract mappings."""

    def __init__(
        self,
        repository: ActusRepository = actus_repository,
        contract_svc: ContractService = contract_service,
    ) -> None:
        self.repository = repository
        self.contract_service = contract_svc

    def generate_mapping(
        self, contract_id: str, status_date: Optional[datetime] = None
    ) -> ActusMappingResponse:
        """Fetch FinancialContract, invoke ACTUS mapper, store and return mapping result."""
        domain_contract = self.contract_service.repository.get_by_id(contract_id)
        if not domain_contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Financial contract with ID '{contract_id}' not found.",
            )

        # Generate ACTUS mapping
        record = ActusMapper.map_contract(domain_contract, status_date=status_date)
        saved = self.repository.save(record)

        actus_resp = (
            ActusContractResponse.model_validate(saved.actus_contract)
            if saved.actus_contract
            else None
        )

        return ActusMappingResponse(
            source_contract_id=saved.source_contract_id,
            mapping_status=saved.mapping_status,
            actus_contract=actus_resp,
            warnings=saved.warnings,
            missing_attributes=saved.missing_attributes,
        )

    def get_mapping(self, contract_id: str) -> ActusMappingResponse:
        """Retrieve previously generated ACTUS mapping for a contract ID."""
        record = self.repository.get_by_source_id(contract_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ACTUS mapping for contract ID '{contract_id}' not found.",
            )

        actus_resp = (
            ActusContractResponse.model_validate(record.actus_contract)
            if record.actus_contract
            else None
        )

        return ActusMappingResponse(
            source_contract_id=record.source_contract_id,
            mapping_status=record.mapping_status,
            actus_contract=actus_resp,
            warnings=record.warnings,
            missing_attributes=record.missing_attributes,
        )


# Global default service instance
actus_service = ActusService()
