"""Financial Contract domain model definitions."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PaymentFrequency(str, Enum):
    """Supported payment frequencies."""

    MONTHLY = "MONTHLY"


class ContractRole(str, Enum):
    """ACTUS-compatible contract roles."""

    RPA = "RPA"  # Real Position Asset / Asset position
    RPL = "RPL"  # Real Position Liability / Liability position


class ContractStatus(str, Enum):
    """Financial contract lifecycle states."""

    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"


class FinancialContract(BaseModel):
    """Domain model representing a normalized financial contract."""

    contract_id: str = Field(..., description="Unique contract identifier (UUID v4)")
    principal: Decimal = Field(..., description="Principal monetary amount")
    currency: str = Field(..., description="Currency code (e.g., INR, USD)")
    annual_interest_rate: Decimal = Field(..., description="Annual interest rate percentage")
    start_date: date = Field(..., description="Contract start / inception date")
    maturity_date: date = Field(..., description="Contract maturity date")
    payment_frequency: PaymentFrequency = Field(..., description="Payment recurrence frequency")
    contract_role: ContractRole = Field(..., description="Contract role / position")
    description: Optional[str] = Field(default=None, description="Optional contract description")
    status: ContractStatus = Field(default=ContractStatus.VALIDATED, description="Contract status")
    created_at: datetime = Field(..., description="UTC creation timestamp")

    model_config = ConfigDict(
        use_enum_values=False,
        arbitrary_types_allowed=True,
    )
