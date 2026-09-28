"""In-memory repository for storing ContractLinkRecord instances."""

from typing import Dict, List, Optional
from app.blockchain.models import ContractLinkRecord


class ContractLinkRepository:
    """In-memory repository managing links between internal FinancialContract IDs and on-chain deployment addresses."""

    def __init__(self) -> None:
        self._storage: Dict[str, ContractLinkRecord] = {}

    def save(self, record: ContractLinkRecord) -> ContractLinkRecord:
        """Store or update a contract link record."""
        self._storage[record.contract_id] = record
        return record

    def get_by_contract_id(self, contract_id: str) -> Optional[ContractLinkRecord]:
        """Retrieve contract link record by internal FinancialContract ID."""
        return self._storage.get(contract_id)

    def get_all(self) -> List[ContractLinkRecord]:
        """Retrieve all stored contract link records."""
        return list(self._storage.values())

    def clear(self) -> None:
        """Clear all contract link records (used for test teardown)."""
        self._storage.clear()


# Global singleton repository instance
contract_link_repository = ContractLinkRepository()
