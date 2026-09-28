"""API routes for ACTUS Contractual Event Generation and Retrieval."""

from fastapi import APIRouter, status

from app.schemas.actus_event import ActusEventGenerationResponse
from app.services.actus_event_service import actus_event_service

router = APIRouter(prefix="/api/v1/contracts", tags=["ACTUS Event Generation"])


@router.post(
    "/{contract_id}/actus/events",
    response_model=ActusEventGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate expected ACTUS contractual events for a contract",
)
def generate_contract_events(contract_id: str) -> ActusEventGenerationResponse:
    """Generate and store expected ACTUS contractual event timeline for a validated contract."""
    return actus_event_service.generate_events_for_contract(contract_id)


@router.get(
    "/{contract_id}/actus/events",
    response_model=ActusEventGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve expected ACTUS contractual events for a contract",
)
def get_contract_events(contract_id: str) -> ActusEventGenerationResponse:
    """Retrieve the generated expected ACTUS contractual event timeline for a contract."""
    return actus_event_service.get_events_for_contract(contract_id)
