"""In-memory repository for storing ContractHash records."""

from typing import Dict, List, Optional
from app.models.contract_hash import ContractHash


class ContractHashRepository:
    """In-memory persistence repository for ContractHash records.
    
    Designed to allow easy replacement with database storage in future phases.
    """

    def __init__(self) -> None:
        self._storage: Dict[str, ContractHash] = {}

    def save(self, record: ContractHash) -> ContractHash:
        """Store or update a contract hash record."""
        self._storage[record.contract_id] = record
        return record

    def get_by_contract_id(self, contract_id: str) -> Optional[ContractHash]:
        """Retrieve a contract hash record by source FinancialContract ID."""
        return self._storage.get(contract_id)

    def get_all(self) -> List[ContractHash]:
        """Retrieve all stored contract hash records."""
        return list(self._storage.values())

    def clear(self) -> None:
        """Clear all stored contract hash records (used for test teardown)."""
        self._storage.clear()


# Global singleton repository instance
contract_hash_repository = ContractHashRepository()
