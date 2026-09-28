"""In-memory repository for storing ACTUS contract mapping records."""

from typing import Dict, List, Optional
from app.models.actus import ActusMappingRecord


class ActusRepository:
    """In-memory persistence repository for ActusMappingRecord.
    
    Designed to allow easy replacement with database storage in future phases.
    """

    def __init__(self) -> None:
        self._storage: Dict[str, ActusMappingRecord] = {}

    def save(self, record: ActusMappingRecord) -> ActusMappingRecord:
        """Store or update an ACTUS mapping record."""
        self._storage[record.source_contract_id] = record
        return record

    def get_by_source_id(self, source_contract_id: str) -> Optional[ActusMappingRecord]:
        """Retrieve an ACTUS mapping record by source FinancialContract ID."""
        return self._storage.get(source_contract_id)

    def get_all(self) -> List[ActusMappingRecord]:
        """Retrieve all stored ACTUS mapping records."""
        return list(self._storage.values())

    def clear(self) -> None:
        """Clear all stored ACTUS mapping records (used for test teardown)."""
        self._storage.clear()


# Global singleton repository instance
actus_repository = ActusRepository()
