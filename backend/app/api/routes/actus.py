"""API routes for ACTUS Contract Mapping generation and retrieval."""

from fastapi import APIRouter, status

from app.schemas.actus import ActusMappingResponse
from app.services.actus_service import actus_service

router = APIRouter(prefix="/api/v1/contracts", tags=["ACTUS Mapping"])


@router.post(
    "/{contract_id}/actus",
    response_model=ActusMappingResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate ACTUS contract mapping for a validated FinancialContract",
)
def generate_actus_mapping(contract_id: str) -> ActusMappingResponse:
    """Generate and store standard ACTUS contract mapping for a validated FinancialContract."""
    return actus_service.generate_mapping(contract_id)


@router.get(
    "/{contract_id}/actus",
    response_model=ActusMappingResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve ACTUS contract mapping for a FinancialContract",
)
def get_actus_mapping(contract_id: str) -> ActusMappingResponse:
    """Retrieve the generated ACTUS contract mapping for a given contract ID."""
    return actus_service.get_mapping(contract_id)
