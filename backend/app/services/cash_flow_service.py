"""Service layer managing cash flow simulation lifecycle and storage."""

from typing import Optional
from fastapi import HTTPException, status

from app.models.cash_flow import CashFlowCalculationStatus
from app.repositories.actus_event_repository import ActusEventRepository, actus_event_repository
from app.repositories.actus_repository import ActusRepository, actus_repository
from app.repositories.cash_flow_repository import CashFlowRepository, cash_flow_repository
from app.schemas.cash_flow import CashFlowResponse, CashFlowSimulationResponse
from app.services.cash_flow_calculator import CashFlowCalculator


class CashFlowService:
    """Business service for calculating and retrieving cash flow simulations."""

    def __init__(
        self,
        cash_flow_repo: CashFlowRepository = cash_flow_repository,
        actus_repo: ActusRepository = actus_repository,
        event_repo: ActusEventRepository = actus_event_repository,
    ) -> None:
        self.repository = cash_flow_repo
        self.actus_repository = actus_repo
        self.event_repository = event_repo

    def calculate_cash_flows(self, contract_id: str) -> CashFlowSimulationResponse:
        """Fetch ACTUS contract and expected events, run cash flow simulation, store and return response."""
        # 1. Fetch ACTUS contract mapping
        actus_record = self.actus_repository.get_by_source_id(contract_id)
        if not actus_record or not actus_record.actus_contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ACTUS mapping for contract ID '{contract_id}' not found. Please generate ACTUS contract mapping first.",
            )

        # 2. Fetch ACTUS events timeline
        event_record = self.event_repository.get_by_contract_id(contract_id)
        if not event_record or not event_record.events:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ACTUS events for contract ID '{contract_id}' not found. Please generate ACTUS events first.",
            )

        # Convert event response schemas back to domain ActusEvent objects for calculator
        from app.models.actus_event import ActusEvent
        domain_events = [ActusEvent.model_validate(ev.model_dump()) for ev in event_record.events]

        # 3. Calculate cash flows
        sim_result = CashFlowCalculator.calculate_cash_flows(actus_record.actus_contract, domain_events)

        # 4. Save result
        saved = self.repository.save(sim_result)

        # 5. Build response schema
        cf_responses = [CashFlowResponse.model_validate(cf) for cf in saved.cash_flows]
        return CashFlowSimulationResponse(
            contract_id=saved.contract_id,
            actus_contract_type=saved.actus_contract_type,
            calculation_status=saved.calculation_status,
            currency=saved.currency,
            initial_principal=saved.initial_principal,
            total_interest=saved.total_interest,
            total_principal=saved.total_principal,
            total_cash_flow=saved.total_cash_flow,
            final_outstanding_principal=saved.final_outstanding_principal,
            cash_flows=cf_responses,
            warnings=saved.warnings,
            missing_attributes=saved.missing_attributes,
        )

    def get_cash_flows(self, contract_id: str) -> CashFlowSimulationResponse:
        """Retrieve previously calculated cash flow simulation for a contract ID."""
        record = self.repository.get_by_contract_id(contract_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cash flow simulation for contract ID '{contract_id}' not found. Please calculate cash flows first.",
            )

        cf_responses = [CashFlowResponse.model_validate(cf) for cf in record.cash_flows]
        return CashFlowSimulationResponse(
            contract_id=record.contract_id,
            actus_contract_type=record.actus_contract_type,
            calculation_status=record.calculation_status,
            currency=record.currency,
            initial_principal=record.initial_principal,
            total_interest=record.total_interest,
            total_principal=record.total_principal,
            total_cash_flow=record.total_cash_flow,
            final_outstanding_principal=record.final_outstanding_principal,
            cash_flows=cf_responses,
            warnings=record.warnings,
            missing_attributes=record.missing_attributes,
        )


# Global default service instance
cash_flow_service = CashFlowService()
