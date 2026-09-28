"""ACTUS Event Generator Service converting ActusContract representations into expected contractual event timelines."""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
import uuid

from app.models.actus import ActusContract
from app.models.actus_event import (
    ActusEvent,
    ActusEventGenerationStatus,
    ActusEventStatus,
    ActusEventType,
)
from app.schemas.actus_event import ActusEventGenerationResponse, ActusEventResponse
from app.services.actus_cycle import format_iso_datetime, generate_cycle_dates, parse_iso_datetime

# Deterministic priority ordering when multiple events occur at the exact same timestamp
EVENT_TYPE_PRIORITY: Dict[ActusEventType, int] = {
    ActusEventType.IED: 1,
    ActusEventType.PR: 2,
    ActusEventType.IP: 3,
    ActusEventType.PP: 4,
    ActusEventType.MD: 5,
}


class ActusEventGenerator:
    """Service for generating deterministic ACTUS expected contractual event timelines."""

    SUPPORTED_CONTRACT_TYPES = {"ANN", "PAM", "LAM"}

    @classmethod
    def generate_events(cls, actus_contract: ActusContract) -> ActusEventGenerationResponse:
        """Generate expected ACTUS contractual events for a given ActusContract model.
        
        Validates contract attributes, checks cycles and anchors, and builds a sorted,
        deterministic event timeline.
        """
        warnings: List[str] = []
        missing_attributes: List[str] = []

        contract_id = actus_contract.contractID
        contract_type = actus_contract.contractType

        # 1. Validate contractType presence
        if not contract_type:
            warnings.append("ACTUS contractType is missing or not set. Human review required.")
            missing_attributes.append("contractType")
            return ActusEventGenerationResponse(
                contract_id=contract_id,
                actus_contract_type=None,
                generation_status=ActusEventGenerationStatus.REQUIRES_REVIEW,
                total_events=0,
                events=[],
                warnings=warnings,
                missing_attributes=missing_attributes,
            )

        # 2. Check if contractType is supported
        if contract_type not in cls.SUPPORTED_CONTRACT_TYPES:
            warnings.append(f"ACTUS contractType '{contract_type}' is not supported for event generation in Phase 4.")
            return ActusEventGenerationResponse(
                contract_id=contract_id,
                actus_contract_type=contract_type,
                generation_status=ActusEventGenerationStatus.UNSUPPORTED,
                total_events=0,
                events=[],
                warnings=warnings,
                missing_attributes=missing_attributes,
            )

        # 3. Check dates
        try:
            start_dt = parse_iso_datetime(actus_contract.initialExchangeDate)
            end_dt = parse_iso_datetime(actus_contract.maturityDate)
        except Exception as exc:
            warnings.append(f"Invalid date format in ACTUS contract: {str(exc)}")
            return ActusEventGenerationResponse(
                contract_id=contract_id,
                actus_contract_type=contract_type,
                generation_status=ActusEventGenerationStatus.INVALID,
                total_events=0,
                events=[],
                warnings=warnings,
                missing_attributes=["initialExchangeDate", "maturityDate"],
            )

        if start_dt >= end_dt:
            warnings.append("initialExchangeDate must be strictly before maturityDate.")
            return ActusEventGenerationResponse(
                contract_id=contract_id,
                actus_contract_type=contract_type,
                generation_status=ActusEventGenerationStatus.INVALID,
                total_events=0,
                events=[],
                warnings=warnings,
                missing_attributes=[],
            )

        # 4. Check Interest Payment Anchor & Cycle
        if not actus_contract.cycleOfInterestPayment:
            warnings.append("cycleOfInterestPayment is missing.")
            missing_attributes.append("cycleOfInterestPayment")

        if not actus_contract.cycleAnchorDateOfInterestPayment:
            warnings.append("cycleAnchorDateOfInterestPayment is missing.")
            missing_attributes.append("cycleAnchorDateOfInterestPayment")

        # 5. Check Principal Redemption Anchor & Cycle for ANN / LAM
        if contract_type in ["ANN", "LAM"]:
            if not actus_contract.cycleOfPrincipalRedemption:
                warnings.append("cycleOfPrincipalRedemption is missing for amortizing contract.")
                missing_attributes.append("cycleOfPrincipalRedemption")
            if not actus_contract.cycleAnchorDateOfPrincipalRedemption:
                warnings.append("cycleAnchorDateOfPrincipalRedemption is missing for amortizing contract.")
                missing_attributes.append("cycleAnchorDateOfPrincipalRedemption")

        if missing_attributes:
            return ActusEventGenerationResponse(
                contract_id=contract_id,
                actus_contract_type=contract_type,
                generation_status=ActusEventGenerationStatus.REQUIRES_REVIEW,
                total_events=0,
                events=[],
                warnings=warnings,
                missing_attributes=missing_attributes,
            )

        # 6. Generate Events Timeline
        raw_events: List[Tuple[datetime, ActusEventType, str]] = []

        # A. Initial Exchange Event (IED)
        raw_events.append((start_dt, ActusEventType.IED, "Initial Principal Exchange"))

        # B. Interest Payment Events (IP)
        if actus_contract.cycleOfInterestPayment and actus_contract.cycleAnchorDateOfInterestPayment:
            anchor_ip_dt = parse_iso_datetime(actus_contract.cycleAnchorDateOfInterestPayment)
            ip_dates = generate_cycle_dates(
                start_date=start_dt,
                end_date=end_dt,
                cycle=actus_contract.cycleOfInterestPayment,
                anchor_date=anchor_ip_dt,
            )
            for ip_dt in ip_dates:
                # Do not duplicate if exactly matches IED start_dt unless anchor differs
                if ip_dt > start_dt and ip_dt <= end_dt:
                    raw_events.append((ip_dt, ActusEventType.IP, "Scheduled Interest Payment"))

        # C. Principal Redemption Events (PR) - ONLY for ANN and LAM
        if contract_type in ["ANN", "LAM"] and actus_contract.cycleOfPrincipalRedemption and actus_contract.cycleAnchorDateOfPrincipalRedemption:
            anchor_pr_dt = parse_iso_datetime(actus_contract.cycleAnchorDateOfPrincipalRedemption)
            pr_dates = generate_cycle_dates(
                start_date=start_dt,
                end_date=end_dt,
                cycle=actus_contract.cycleOfPrincipalRedemption,
                anchor_date=anchor_pr_dt,
            )
            for pr_dt in pr_dates:
                if pr_dt > start_dt and pr_dt <= end_dt:
                    raw_events.append((pr_dt, ActusEventType.PR, "Scheduled Principal Redemption"))

        # D. Maturity Event (MD)
        raw_events.append((end_dt, ActusEventType.MD, "Contract Maturity"))

        # 7. Sort Events Deterministically by (event_time, EVENT_TYPE_PRIORITY)
        raw_events.sort(key=lambda x: (x[0], EVENT_TYPE_PRIORITY[x[1]]))

        # 8. Assign UUIDs, 1-based Sequences, and Build Domain Response
        event_models: List[ActusEventResponse] = []
        for idx, (ev_time, ev_type, ev_ref) in enumerate(raw_events, start=1):
            event_obj = ActusEvent(
                event_id=str(uuid.uuid4()),
                contract_id=contract_id,
                event_type=ev_type,
                event_time=format_iso_datetime(ev_time),
                sequence=idx,
                event_status=ActusEventStatus.EXPECTED,
                source_actus_contract_id=actus_contract.contractID,
                currency=actus_contract.currency,
                notional_principal=actus_contract.notionalPrincipal,
                nominal_interest_rate=actus_contract.nominalInterestRate,
                event_reference=ev_ref,
            )
            event_models.append(ActusEventResponse.model_validate(event_obj))

        return ActusEventGenerationResponse(
            contract_id=contract_id,
            actus_contract_type=contract_type,
            generation_status=ActusEventGenerationStatus.GENERATED,
            total_events=len(event_models),
            events=event_models,
            warnings=warnings,
            missing_attributes=[],
        )
