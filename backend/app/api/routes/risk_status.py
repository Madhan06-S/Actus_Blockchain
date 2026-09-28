"""API routes for financial risk status layer and payment reconciliation evaluation."""

from fastapi import APIRouter, HTTPException, status

from app.blockchain.exceptions import ContractNotLinkedError
from app.schemas.risk_status import ContractRiskStatusResponse
from app.services.risk_status_service import risk_status_service

router = APIRouter(prefix="/api/v1/contracts", tags=["Financial Risk & Status"])


@router.get(
    "/{contract_id}/status",
    response_model=ContractRiskStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get financial risk/status for a contract",
)
def get_contract_risk_status(contract_id: str) -> ContractRiskStatusResponse:
    """Calculate and return overall rule-based financial status and reconciliation indicators for a contract."""
    try:
        domain_status = risk_status_service.calculate_risk_status(contract_id)
        return ContractRiskStatusResponse.model_validate(domain_status)
    except ContractNotLinkedError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=err.message,
        ) from err
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to evaluate risk status: {str(exc)}",
        ) from exc
