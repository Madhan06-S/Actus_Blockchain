"""Pydantic schemas for Financial Contract API request and response models."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.contract import ContractRole, ContractStatus, PaymentFrequency


class FinancialContractCreate(BaseModel):
    """Request schema for creating a new financial contract."""

    principal: Decimal = Field(
        ...,
        description="Principal monetary amount (must be positive)",
        json_schema_extra={"example": 100000},
    )
    currency: str = Field(
        ...,
        description="Currency code (e.g., INR, USD)",
        json_schema_extra={"example": "INR"},
    )
    annual_interest_rate: Decimal = Field(
        ...,
        description="Annual fixed interest rate percentage (must be non-negative)",
        json_schema_extra={"example": 10.0},
    )
    start_date: date = Field(
        ...,
        description="Contract start date (YYYY-MM-DD)",
        json_schema_extra={"example": "2027-01-01"},
    )
    maturity_date: date = Field(
        ...,
        description="Contract maturity date (YYYY-MM-DD)",
        json_schema_extra={"example": "2029-01-01"},
    )
    payment_frequency: PaymentFrequency = Field(
        ...,
        description="Payment frequency recurrence",
        json_schema_extra={"example": "MONTHLY"},
    )
    contract_role: ContractRole = Field(
        ...,
        description="Contract role / position",
        json_schema_extra={"example": "RPA"},
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional description",
        json_schema_extra={"example": "Example fixed-rate amortizing loan"},
    )

    @field_validator("principal")
    @classmethod
    def validate_principal(cls, v: Decimal) -> Decimal:
        """Ensure principal is strictly greater than 0."""
        if v <= Decimal("0"):
            raise ValueError("Principal must be greater than 0")
        return v

    @field_validator("annual_interest_rate")
    @classmethod
    def validate_interest_rate(cls, v: Decimal) -> Decimal:
        """Ensure annual interest rate is non-negative."""
        if v < Decimal("0"):
            raise ValueError("Annual interest rate cannot be negative")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Ensure currency is not empty or whitespace-only."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Currency cannot be empty")
        return stripped.upper()

    @model_validator(mode="after")
    def validate_dates(self) -> "FinancialContractCreate":
        """Ensure start date is strictly before maturity date."""
        if self.start_date >= self.maturity_date:
            raise ValueError("Maturity date must be strictly after start date")
        return self


class FinancialContractResponse(BaseModel):
    """Response schema for a single financial contract."""

    contract_id: str = Field(..., description="Unique contract identifier (UUID v4)")
    principal: Decimal = Field(..., description="Principal monetary amount")
    currency: str = Field(..., description="Currency code")
    annual_interest_rate: Decimal = Field(..., description="Annual fixed interest rate percentage")
    start_date: date = Field(..., description="Contract start date")
    maturity_date: date = Field(..., description="Contract maturity date")
    payment_frequency: PaymentFrequency = Field(..., description="Payment frequency")
    contract_role: ContractRole = Field(..., description="Contract role")
    description: Optional[str] = Field(default=None, description="Contract description")
    status: ContractStatus = Field(..., description="Contract status")
    created_at: datetime = Field(..., description="UTC creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class FinancialContractListResponse(BaseModel):
    """Response schema for listing financial contracts."""

    total: int = Field(..., description="Total count of contracts")
    contracts: List[FinancialContractResponse] = Field(..., description="List of financial contracts")
