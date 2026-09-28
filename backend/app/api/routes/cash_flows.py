"""API routes for ACTUS Expected Cash Flow Simulation."""

from fastapi import APIRouter, status

from app.schemas.cash_flow import CashFlowSimulationResponse
from app.services.cash_flow_service import cash_flow_service

router = APIRouter(prefix="/api/v1/contracts", tags=["ACTUS Cash Flows"])


@router.post(
    "/{contract_id}/actus/cash-flows",
    response_model=CashFlowSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate expected cash flows for a contract",
)
def calculate_contract_cash_flows(contract_id: str) -> CashFlowSimulationResponse:
    """Calculate and store expected monetary cash flow simulation for an ACTUS contract."""
    return cash_flow_service.calculate_cash_flows(contract_id)


@router.get(
    "/{contract_id}/actus/cash-flows",
    response_model=CashFlowSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve expected cash flows for a contract",
)
def get_contract_cash_flows(contract_id: str) -> CashFlowSimulationResponse:
    """Retrieve previously calculated expected cash flow simulation for a contract."""
    return cash_flow_service.get_cash_flows(contract_id)
