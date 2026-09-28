"""In-memory repository for storing CashFlowSimulationResult records."""

from typing import Dict, List, Optional
from app.models.cash_flow import CashFlowSimulationResult


class CashFlowRepository:
    """In-memory storage repository for cash flow simulation results."""

    def __init__(self) -> None:
        self._storage: Dict[str, CashFlowSimulationResult] = {}

    def save(self, result: CashFlowSimulationResult) -> CashFlowSimulationResult:
        """Store or update a cash flow simulation result."""
        self._storage[result.contract_id] = result
        return result

    def get_by_contract_id(self, contract_id: str) -> Optional[CashFlowSimulationResult]:
        """Retrieve stored cash flow simulation result by contract ID."""
        return self._storage.get(contract_id)

    def get_all(self) -> List[CashFlowSimulationResult]:
        """Retrieve all stored cash flow simulation results."""
        return list(self._storage.values())

    def clear(self) -> None:
        """Clear all stored cash flow simulation records (used for test teardown)."""
        self._storage.clear()


# Global singleton instance
cash_flow_repository = CashFlowRepository()
