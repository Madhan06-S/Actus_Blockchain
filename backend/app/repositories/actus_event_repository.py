"""In-memory repository for storing ACTUS event generation responses."""

from typing import Dict, List, Optional
from app.schemas.actus_event import ActusEventGenerationResponse


class ActusEventRepository:
    """In-memory repository for storing generated ACTUS event timelines."""

    def __init__(self) -> None:
        self._storage: Dict[str, ActusEventGenerationResponse] = {}

    def save(self, record: ActusEventGenerationResponse) -> ActusEventGenerationResponse:
        """Store or update an ACTUS event generation response."""
        self._storage[record.contract_id] = record
        return record

    def get_by_contract_id(self, contract_id: str) -> Optional[ActusEventGenerationResponse]:
        """Retrieve generated ACTUS events by contract ID."""
        return self._storage.get(contract_id)

    def get_all(self) -> List[ActusEventGenerationResponse]:
        """Retrieve all stored ACTUS event generation records."""
        return list(self._storage.values())

    def clear(self) -> None:
        """Clear all stored ACTUS event records (used for test teardown)."""
        self._storage.clear()


# Global singleton repository instance
actus_event_repository = ActusEventRepository()
