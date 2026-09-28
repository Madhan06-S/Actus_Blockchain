"""Cash Flow Calculator service implementing ACTUS ANN amortization and event cash flow simulations."""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import math
from typing import Dict, List, Optional, Tuple
import uuid

from app.models.actus import ActusContract
from app.models.actus_event import ActusEvent
from app.models.cash_flow import (
    CashFlow,
    CashFlowCalculationStatus,
    CashFlowDirection,
    CashFlowSimulationResult,
)

# Currency precision quantization helper (e.g., 0.01 for 2 decimal places)
TWOPLACES = Decimal("0.01")


def quantize_currency(value: Decimal) -> Decimal:
    """Quantize a Decimal value to 2 decimal currency places using ROUND_HALF_UP."""
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def get_cash_flow_direction(contract_role: str, event_type: str) -> Tuple[CashFlowDirection, Decimal]:
    """Determine cash flow direction and sign multiplier based on ACTUS contractRole.
    
    For RPA (Receive Position Asset / Lender / Investor):
      - IED (Initial Exchange): OUTFLOW (-1 multiplier, disburser pays principal out)
      - Repayments (IP, PR, MD): INFLOW (+1 multiplier, receives repayments)
    
    For RPL (Pay Position Liability / Borrower):
      - IED (Initial Exchange): INFLOW (+1 multiplier, receives loan principal)
      - Repayments (IP, PR, MD): OUTFLOW (-1 multiplier, pays debt service)
    """
    role = (contract_role or "RPA").upper()
    if role == "RPA":
        if event_type == "IED":
            return CashFlowDirection.OUTFLOW, Decimal("-1")
        else:
            return CashFlowDirection.INFLOW, Decimal("1")
    elif role == "RPL":
        if event_type == "IED":
            return CashFlowDirection.INFLOW, Decimal("1")
        else:
            return CashFlowDirection.OUTFLOW, Decimal("-1")
    else:
        return CashFlowDirection.INFLOW, Decimal("1")


class CashFlowCalculator:
    """Calculator for ACTUS contractual event expected cash flows."""

    SUPPORTED_CONTRACT_TYPES = {"ANN"}

    @classmethod
    def calculate_cash_flows(
        cls, actus_contract: ActusContract, events: List[ActusEvent]
    ) -> CashFlowSimulationResult:
        """Calculate expected monetary cash flows from an ActusContract and Phase 4 events timeline.
        
        Maintains opening/closing principal state across payment periods for ANN amortizing contracts.
        Reconciles final maturity payment so outstanding balance reaches 0.00.
        """
        warnings: List[str] = []
        missing_attributes: List[str] = []

        contract_id = actus_contract.contractID
        contract_type = actus_contract.contractType
        currency = actus_contract.currency
        principal = actus_contract.notionalPrincipal
        annual_rate = actus_contract.nominalInterestRate
        role = actus_contract.contractRole

        # 1. Validate supported contractType
        if not contract_type or contract_type not in cls.SUPPORTED_CONTRACT_TYPES:
            warnings.append(
                f"Cash flow simulation for ACTUS contractType '{contract_type}' is not supported in Phase 5. Only 'ANN' is supported."
            )
            return CashFlowSimulationResult(
                contract_id=contract_id,
                actus_contract_type=contract_type,
                calculation_status=CashFlowCalculationStatus.CALCULATION_UNSUPPORTED,
                currency=currency,
                initial_principal=principal,
                total_interest=Decimal("0.00"),
                total_principal=Decimal("0.00"),
                total_cash_flow=Decimal("0.00"),
                final_outstanding_principal=principal,
                cash_flows=[],
                warnings=warnings,
                missing_attributes=[],
                created_at=datetime.now(timezone.utc),
            )

        # 2. Validate dayCountConvention
        if not actus_contract.dayCountConvention:
            warnings.append("Day-count convention (dayCountConvention) is missing from ACTUS contract mapping.")
            missing_attributes.append("dayCountConvention")
            return CashFlowSimulationResult(
                contract_id=contract_id,
                actus_contract_type=contract_type,
                calculation_status=CashFlowCalculationStatus.CALCULATION_REQUIRES_REVIEW,
                currency=currency,
                initial_principal=principal,
                total_interest=Decimal("0.00"),
                total_principal=Decimal("0.00"),
                total_cash_flow=Decimal("0.00"),
                final_outstanding_principal=principal,
                cash_flows=[],
                warnings=warnings,
                missing_attributes=missing_attributes,
                created_at=datetime.now(timezone.utc),
            )

        # 3. Validate principal and interest rate numeric values
        if principal <= Decimal("0"):
            warnings.append("notionalPrincipal must be strictly positive for cash flow calculation.")
            return CashFlowSimulationResult(
                contract_id=contract_id,
                actus_contract_type=contract_type,
                calculation_status=CashFlowCalculationStatus.CALCULATION_INVALID,
                currency=currency,
                initial_principal=principal,
                total_interest=Decimal("0.00"),
                total_principal=Decimal("0.00"),
                total_cash_flow=Decimal("0.00"),
                final_outstanding_principal=principal,
                cash_flows=[],
                warnings=warnings,
                missing_attributes=[],
                created_at=datetime.now(timezone.utc),
            )

        if annual_rate < Decimal("0"):
            warnings.append("nominalInterestRate cannot be negative for cash flow calculation.")
            return CashFlowSimulationResult(
                contract_id=contract_id,
                actus_contract_type=contract_type,
                calculation_status=CashFlowCalculationStatus.CALCULATION_INVALID,
                currency=currency,
                initial_principal=principal,
                total_interest=Decimal("0.00"),
                total_principal=Decimal("0.00"),
                total_cash_flow=Decimal("0.00"),
                final_outstanding_principal=principal,
                cash_flows=[],
                warnings=warnings,
                missing_attributes=[],
                created_at=datetime.now(timezone.utc),
            )

        # 4. Process events timeline and calculate cash flows
        cash_flow_list: List[CashFlow] = []

        # Find IED event
        ied_events = [e for e in events if e.event_type == "IED"]
        if ied_events:
            ied_ev = ied_events[0]
            direction, sign = get_cash_flow_direction(role, "IED")
            ied_cf = CashFlow(
                cash_flow_id=str(uuid.uuid4()),
                contract_id=contract_id,
                event_id=ied_ev.event_id,
                event_type="IED",
                event_time=ied_ev.event_time,
                currency=currency,
                opening_principal=Decimal("0.00"),
                interest_amount=Decimal("0.00"),
                principal_amount=principal,
                total_amount=principal,
                closing_principal=principal,
                cash_flow_direction=direction,
                net_cash_flow=sign * principal,
                calculation_reference="Initial Principal Disbursement",
            )
            cash_flow_list.append(ied_cf)

        # Group repayment payment dates (PR & IP occurring on same timestamps)
        payment_timestamps: List[str] = []
        event_map_by_time: Dict[str, List[ActusEvent]] = {}
        for ev in events:
            if ev.event_type in ["IP", "PR"]:
                if ev.event_time not in event_map_by_time:
                    payment_timestamps.append(ev.event_time)
                    event_map_by_time[ev.event_time] = []
                event_map_by_time[ev.event_time].append(ev)

        N = len(payment_timestamps)
        if N == 0:
            warnings.append("No repayment payment events found in events timeline.")
            return CashFlowSimulationResult(
                contract_id=contract_id,
                actus_contract_type=contract_type,
                calculation_status=CashFlowCalculationStatus.CALCULATION_REQUIRES_REVIEW,
                currency=currency,
                initial_principal=principal,
                total_interest=Decimal("0.00"),
                total_principal=Decimal("0.00"),
                total_cash_flow=Decimal("0.00"),
                final_outstanding_principal=principal,
                cash_flows=cash_flow_list,
                warnings=warnings,
                missing_attributes=[],
                created_at=datetime.now(timezone.utc),
            )

        # Calculate periodic interest rate r = annual_rate / 12
        r = annual_rate / Decimal("12")

        # Calculate Annuity PMT = P * [r*(1+r)^N] / [(1+r)^N - 1]
        if r == Decimal("0"):
            pmt = principal / Decimal(str(N))
        else:
            r_float = float(r)
            pmt_float = float(principal) * (r_float * (1 + r_float)**N) / ((1 + r_float)**N - 1)
            pmt = Decimal(str(pmt_float))

        opening_balance = principal
        accumulated_interest = Decimal("0.00")
        accumulated_principal = Decimal("0.00")

        direction, sign = get_cash_flow_direction(role, "IP")

        for idx, ev_time in enumerate(payment_timestamps, start=1):
            linked_events = event_map_by_time[ev_time]
            primary_event_id = linked_events[0].event_id if linked_events else None

            # Calculate interest portion
            interest_port = quantize_currency(opening_balance * r)

            # Calculate principal portion
            if idx == N:
                # Final maturity period: exact principal reconciliation
                principal_port = opening_balance
            else:
                principal_port = quantize_currency(pmt - interest_port)
                if principal_port > opening_balance:
                    principal_port = opening_balance

            total_pmt = interest_port + principal_port
            closing_balance = quantize_currency(opening_balance - principal_port)

            cf_obj = CashFlow(
                cash_flow_id=str(uuid.uuid4()),
                contract_id=contract_id,
                event_id=primary_event_id,
                event_type="PR_IP",
                event_time=ev_time,
                currency=currency,
                opening_principal=quantize_currency(opening_balance),
                interest_amount=interest_port,
                principal_amount=principal_port,
                total_amount=total_pmt,
                closing_principal=closing_balance,
                cash_flow_direction=direction,
                net_cash_flow=quantize_currency(sign * total_pmt),
                calculation_reference=f"Periodic Payment {idx} of {N}",
            )
            cash_flow_list.append(cf_obj)

            accumulated_interest += interest_port
            accumulated_principal += principal_port
            opening_balance = closing_balance

        # Find MD event if present
        md_events = [e for e in events if e.event_type == "MD"]
        if md_events:
            md_ev = md_events[0]
            md_cf = CashFlow(
                cash_flow_id=str(uuid.uuid4()),
                contract_id=contract_id,
                event_id=md_ev.event_id,
                event_type="MD",
                event_time=md_ev.event_time,
                currency=currency,
                opening_principal=opening_balance,
                interest_amount=Decimal("0.00"),
                principal_amount=Decimal("0.00"),
                total_amount=Decimal("0.00"),
                closing_principal=opening_balance,
                cash_flow_direction=CashFlowDirection.NEUTRAL,
                net_cash_flow=Decimal("0.00"),
                calculation_reference="Contract Maturity Reconciled",
            )
            cash_flow_list.append(md_cf)

        total_aggregate_cash_flow = quantize_currency(accumulated_interest + accumulated_principal)

        return CashFlowSimulationResult(
            contract_id=contract_id,
            actus_contract_type=contract_type,
            calculation_status=CashFlowCalculationStatus.CALCULATED,
            currency=currency,
            initial_principal=quantize_currency(principal),
            total_interest=quantize_currency(accumulated_interest),
            total_principal=quantize_currency(accumulated_principal),
            total_cash_flow=total_aggregate_cash_flow,
            final_outstanding_principal=opening_balance,
            cash_flows=cash_flow_list,
            warnings=warnings,
            missing_attributes=[],
            created_at=datetime.now(timezone.utc),
        )
