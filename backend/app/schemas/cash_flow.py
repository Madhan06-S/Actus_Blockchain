"""Pydantic schemas for Cash Flow API request and response models."""

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.cash_flow import CashFlowCalculationStatus, CashFlowDirection


class CashFlowResponse(BaseModel):
    """Schema for an individual calculated monetary cash flow."""

    cash_flow_id: str = Field(..., description="Unique cash flow identifier")
    contract_id: str = Field(..., description="Associated contract ID")
    event_id: Optional[str] = Field(default=None, description="Linked Phase 4 event ID")
    event_type: str = Field(..., description="ACTUS event type (IED, IP, PR, MD)")
    event_time: str = Field(..., description="ISO 8601 UTC timestamp")
    currency: str = Field(..., description="ISO Currency Code")
    opening_principal: Decimal = Field(..., description="Opening principal balance")
    interest_amount: Decimal = Field(..., description="Interest portion")
    principal_amount: Decimal = Field(..., description="Principal portion")
    total_amount: Decimal = Field(..., description="Total cash flow amount")
    closing_principal: Decimal = Field(..., description="Closing principal balance")
    cash_flow_direction: CashFlowDirection = Field(..., description="Cash movement direction")
    net_cash_flow: Decimal = Field(..., description="Signed monetary amount (+ INFLOW, - OUTFLOW)")
    calculation_reference: Optional[str] = Field(default=None, description="Reference note")

    model_config = ConfigDict(from_attributes=True)


class CashFlowSimulationResponse(BaseModel):
    """Schema representing the overall cash flow simulation response."""

    contract_id: str = Field(..., description="Associated contract ID")
    actus_contract_type: Optional[str] = Field(default=None, description="ACTUS contract type")
    calculation_status: CashFlowCalculationStatus = Field(..., description="Calculation status")
    currency: str = Field(..., description="ISO Currency Code")
    initial_principal: Decimal = Field(..., description="Initial principal amount")
    total_interest: Decimal = Field(..., description="Total interest paid")
    total_principal: Decimal = Field(..., description="Total principal repaid")
    total_cash_flow: Decimal = Field(..., description="Total aggregate cash flow")
    final_outstanding_principal: Decimal = Field(..., description="Final outstanding balance")
    cash_flows: List[CashFlowResponse] = Field(default_factory=list, description="List of calculated cash flows")
    warnings: List[str] = Field(default_factory=list, description="Calculation warnings or review notes")
    missing_attributes: List[str] = Field(default_factory=list, description="Missing attributes preventing calculation")

    model_config = ConfigDict(from_attributes=True)
