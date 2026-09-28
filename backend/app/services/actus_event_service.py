"""Service layer for managing ACTUS event generation lifecycle and storage."""

from typing import Optional
from fastapi import HTTPException, status

from app.repositories.actus_event_repository import ActusEventRepository, actus_event_repository
from app.repositories.actus_repository import ActusRepository, actus_repository
from app.schemas.actus_event import ActusEventGenerationResponse
from app.services.actus_event_generator import ActusEventGenerator


class ActusEventService:
    """Business service for generating and retrieving ACTUS contractual event timelines."""

    def __init__(
        self,
        event_repo: ActusEventRepository = actus_event_repository,
        actus_repo: ActusRepository = actus_repository,
    ) -> None:
        self.event_repository = event_repo
        self.actus_repository = actus_repo

    def generate_events_for_contract(self, contract_id: str) -> ActusEventGenerationResponse:
        """Fetch stored ACTUS mapping, generate expected contractual events, store and return response."""
        actus_record = self.actus_repository.get_by_source_id(contract_id)
        if not actus_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ACTUS contract mapping for contract ID '{contract_id}' not found. Please generate ACTUS mapping first.",
            )

        if not actus_record.actus_contract:
            return ActusEventGenerationResponse(
                contract_id=contract_id,
                actus_contract_type=None,
                generation_status=actus_record.mapping_status.value if hasattr(actus_record.mapping_status, "value") else str(actus_record.mapping_status),
                total_events=0,
                events=[],
                warnings=actus_record.warnings or ["ACTUS contract model is missing."],
                missing_attributes=actus_record.missing_attributes or [],
            )

        # Generate event timeline
        result = ActusEventGenerator.generate_events(actus_record.actus_contract)

        # Store result in repository
        saved = self.event_repository.save(result)
        return saved

    def get_events_for_contract(self, contract_id: str) -> ActusEventGenerationResponse:
        """Retrieve stored ACTUS event timeline for a contract ID."""
        record = self.event_repository.get_by_contract_id(contract_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ACTUS events for contract ID '{contract_id}' not found. Please generate events first.",
            )
        return record


# Global default service instance
actus_event_service = ActusEventService()
