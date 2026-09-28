"""ACTUS domain models and mapping status definitions."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ActusMappingStatus(str, Enum):
    """ACTUS contract mapping evaluation status."""

    MAPPED = "MAPPED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    UNSUPPORTED = "UNSUPPORTED"
    INVALID = "INVALID"


class ActusContract(BaseModel):
    """Domain model representing ACTUS contract attributes based on the official ACTUS Data Dictionary."""

    contractID: str = Field(..., description="Unique ACTUS contract identifier")
    contractType: Optional[str] = Field(default=None, description="ACTUS contract type (e.g., ANN, PAM, LAM)")
    contractRole: str = Field(..., description="ACTUS contract role (e.g., RPA, RPL)")
    currency: str = Field(..., description="ISO Currency Code (e.g., INR, USD)")
    notionalPrincipal: Decimal = Field(..., description="Notional principal amount")
    nominalInterestRate: Decimal = Field(..., description="Nominal interest rate as a fractional value (e.g., 0.10 for 10%)")
    initialExchangeDate: str = Field(..., description="Initial exchange / start date (ISO 8601)")
    maturityDate: str = Field(..., description="Contract maturity date (ISO 8601)")
    statusDate: str = Field(..., description="Status evaluation timestamp (ISO 8601)")
    cycleOfInterestPayment: Optional[str] = Field(default=None, description="Interest payment cycle (e.g., P1M)")
    cycleAnchorDateOfInterestPayment: Optional[str] = Field(default=None, description="Interest cycle anchor date")
    cycleOfPrincipalRedemption: Optional[str] = Field(default=None, description="Principal redemption cycle (e.g., P1M)")
    cycleAnchorDateOfPrincipalRedemption: Optional[str] = Field(default=None, description="Principal redemption anchor date")
    dayCountConvention: Optional[str] = Field(default=None, description="Day count convention (e.g., 30E360)")
    interestCalculationBase: Optional[str] = Field(default=None, description="Interest calculation base")

    model_config = ConfigDict(use_enum_values=False)


class ActusMappingRecord(BaseModel):
    """Record storing an ACTUS mapping result for a FinancialContract."""

    source_contract_id: str = Field(..., description="Source FinancialContract ID")
    mapping_status: ActusMappingStatus = Field(..., description="ACTUS mapping evaluation status")
    actus_contract: Optional[ActusContract] = Field(default=None, description="Mapped ACTUS contract model")
    warnings: List[str] = Field(default_factory=list, description="Mapping warnings or review notes")
    missing_attributes: List[str] = Field(default_factory=list, description="List of unmapped or missing ACTUS attributes")
    created_at: datetime = Field(..., description="UTC creation timestamp")
