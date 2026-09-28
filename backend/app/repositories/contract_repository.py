"""In-memory repository for Financial Contracts."""

from typing import Dict, List, Optional
from app.models.contract import FinancialContract


class ContractRepository:
    """In-memory storage repository for Financial Contracts.
    
    Designed with a clean interface to allow replacing with a PostgreSQL repository
    in future phases without altering business service logic.
    """

    def __init__(self) -> None:
        self._storage: Dict[str, FinancialContract] = {}

    def save(self, contract: FinancialContract) -> FinancialContract:
        """Store or update a financial contract in memory."""
        self._storage[contract.contract_id] = contract
        return contract

    def get_by_id(self, contract_id: str) -> Optional[FinancialContract]:
        """Retrieve a contract by its unique ID."""
        return self._storage.get(contract_id)

    def get_all(self) -> List[FinancialContract]:
        """Retrieve all stored financial contracts."""
        return list(self._storage.values())

    def clear(self) -> None:
        """Clear all stored contracts (primarily used for test teardown)."""
        self._storage.clear()


# Global singleton repository instance for Phase 1 in-memory persistence
contract_repository = ContractRepository()
