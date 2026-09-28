"""Pydantic schemas for ACTUS API request and response models."""

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.actus import ActusMappingStatus


class ActusContractResponse(BaseModel):
    """Schema representing an ACTUS contract object in standard JSON format."""

    contractID: str = Field(..., description="Unique ACTUS contract identifier")
    contractType: Optional[str] = Field(default=None, description="ACTUS contract type (e.g., ANN, PAM, LAM)")
    contractRole: str = Field(..., description="ACTUS contract role (e.g., RPA, RPL)")
    currency: str = Field(..., description="ISO Currency Code (e.g., INR, USD)")
    notionalPrincipal: Decimal = Field(..., description="Notional principal amount")
    nominalInterestRate: Decimal = Field(..., description="Nominal interest rate as a fraction (e.g., 0.10)")
    initialExchangeDate: str = Field(..., description="Initial exchange date (ISO 8601)")
    maturityDate: str = Field(..., description="Contract maturity date (ISO 8601)")
    statusDate: str = Field(..., description="Status evaluation timestamp (ISO 8601)")
    cycleOfInterestPayment: Optional[str] = Field(default=None, description="Interest payment cycle")
    cycleAnchorDateOfInterestPayment: Optional[str] = Field(default=None, description="Interest cycle anchor date")
    cycleOfPrincipalRedemption: Optional[str] = Field(default=None, description="Principal redemption cycle")
    cycleAnchorDateOfPrincipalRedemption: Optional[str] = Field(default=None, description="Principal redemption anchor date")
    dayCountConvention: Optional[str] = Field(default=None, description="Day count convention")
    interestCalculationBase: Optional[str] = Field(default=None, description="Interest calculation base")

    model_config = ConfigDict(from_attributes=True)


class ActusMappingResponse(BaseModel):
    """Schema representing the overall ACTUS mapping result response."""

    source_contract_id: str = Field(..., description="Source FinancialContract ID")
    mapping_status: ActusMappingStatus = Field(..., description="ACTUS mapping evaluation status")
    actus_contract: Optional[ActusContractResponse] = Field(default=None, description="Mapped ACTUS contract payload")
    warnings: List[str] = Field(default_factory=list, description="Mapping warnings or human review notes")
    missing_attributes: List[str] = Field(default_factory=list, description="List of unmapped/missing ACTUS attributes")

    model_config = ConfigDict(from_attributes=True)
