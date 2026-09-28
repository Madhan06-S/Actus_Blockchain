"""Service layer for Financial Contract creation, normalization, and retrieval."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from app.models.contract import ContractStatus, FinancialContract
from app.repositories.contract_repository import ContractRepository, contract_repository
from app.schemas.contract import (
    FinancialContractCreate,
    FinancialContractListResponse,
    FinancialContractResponse,
)


class ContractService:
    """Business service for financial contract lifecycle management."""

    def __init__(self, repository: ContractRepository = contract_repository) -> None:
        self.repository = repository

    def create_contract(self, payload: FinancialContractCreate) -> FinancialContractResponse:
        """Create, validate, normalize, and store a financial contract.
        
        Generates a unique UUID v4 contract_id and UTC created_at timestamp.
        """
        contract_id = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc)

        # Construct normalized domain model
        domain_contract = FinancialContract(
            contract_id=contract_id,
            principal=payload.principal,
            currency=payload.currency,
            annual_interest_rate=payload.annual_interest_rate,
            start_date=payload.start_date,
            maturity_date=payload.maturity_date,
            payment_frequency=payload.payment_frequency,
            contract_role=payload.contract_role,
            description=payload.description,
            status=ContractStatus.VALIDATED,
            created_at=now_utc,
        )

        # Store contract in repository
        saved_contract = self.repository.save(domain_contract)

        # NOTE FOR FUTURE PHASES:
        # Here is the ACTUS integration boundary. Future phases will invoke:
        # actus_contract = actus_service.convert(saved_contract)

        return FinancialContractResponse.model_validate(saved_contract)

    def get_contract_by_id(self, contract_id: str) -> Optional[FinancialContractResponse]:
        """Fetch contract by ID, returning response schema or None if missing."""
        contract = self.repository.get_by_id(contract_id)
        if not contract:
            return None
        return FinancialContractResponse.model_validate(contract)

    def list_contracts(self) -> FinancialContractListResponse:
        """Fetch all stored financial contracts."""
        contracts = self.repository.get_all()
        responses = [FinancialContractResponse.model_validate(c) for c in contracts]
        return FinancialContractListResponse(total=len(responses), contracts=responses)


# Global default service instance
contract_service = ContractService()
