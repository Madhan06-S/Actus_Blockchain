"""Cash flow simulation domain models and status enums."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CashFlowCalculationStatus(str, Enum):
    """Status of cash flow simulation calculation."""

    CALCULATED = "CALCULATED"
    CALCULATION_REQUIRES_REVIEW = "CALCULATION_REQUIRES_REVIEW"
    CALCULATION_UNSUPPORTED = "CALCULATION_UNSUPPORTED"
    CALCULATION_INVALID = "CALCULATION_INVALID"


class CashFlowDirection(str, Enum):
    """Direction of money movement from the perspective of the contract position."""

    INFLOW = "INFLOW"
    OUTFLOW = "OUTFLOW"
    NEUTRAL = "NEUTRAL"


class CashFlow(BaseModel):
    """Domain model representing a calculated monetary cash flow for an event."""

    cash_flow_id: str = Field(..., description="Unique cash flow identifier (UUID v4)")
    contract_id: str = Field(..., description="Associated contract ID")
    event_id: Optional[str] = Field(default=None, description="Linked Phase 4 event ID")
    event_type: str = Field(..., description="ACTUS event type (IED, IP, PR, MD)")
    event_time: str = Field(..., description="ISO 8601 UTC timestamp of cash flow")
    currency: str = Field(..., description="ISO Currency Code")
    opening_principal: Decimal = Field(..., description="Opening outstanding principal balance")
    interest_amount: Decimal = Field(..., description="Interest payment portion")
    principal_amount: Decimal = Field(..., description="Principal redemption portion")
    total_amount: Decimal = Field(..., description="Total payment amount for this cash flow")
    closing_principal: Decimal = Field(..., description="Closing outstanding principal balance")
    cash_flow_direction: CashFlowDirection = Field(..., description="Direction of cash movement")
    net_cash_flow: Decimal = Field(..., description="Signed monetary net cash flow (+ for INFLOW, - for OUTFLOW)")
    calculation_reference: Optional[str] = Field(default=None, description="Calculation reference note")

    model_config = ConfigDict(use_enum_values=False)


class CashFlowSimulationResult(BaseModel):
    """Domain model representing the full cash flow simulation result for a contract."""

    contract_id: str = Field(..., description="Associated contract ID")
    actus_contract_type: Optional[str] = Field(default=None, description="ACTUS contract type")
    calculation_status: CashFlowCalculationStatus = Field(..., description="Simulation calculation status")
    currency: str = Field(..., description="ISO Currency Code")
    initial_principal: Decimal = Field(..., description="Initial principal disbursement")
    total_interest: Decimal = Field(..., description="Total aggregate interest calculated")
    total_principal: Decimal = Field(..., description="Total aggregate principal redeemed")
    total_cash_flow: Decimal = Field(..., description="Total aggregate monetary cash flow")
    final_outstanding_principal: Decimal = Field(..., description="Final remaining principal balance")
    cash_flows: List[CashFlow] = Field(default_factory=list, description="Ordered timeline of cash flows")
    warnings: List[str] = Field(default_factory=list, description="Simulation warnings or notes")
    missing_attributes: List[str] = Field(default_factory=list, description="Missing attributes preventing calculation")
    created_at: datetime = Field(..., description="UTC creation timestamp")

    model_config = ConfigDict(use_enum_values=False)
