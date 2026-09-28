"""ACTUS Event domain models and enums."""

from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ActusEventType(str, Enum):
    """ACTUS contractual event types."""

    IED = "IED"  # Initial Exchange Date
    IP = "IP"    # Interest Payment
    PR = "PR"    # Principal Redemption (Scheduled)
    PP = "PP"    # Principal Prepayment (Unscheduled / Prepayment condition)
    MD = "MD"    # Maturity Date


class ActusEventStatus(str, Enum):
    """Lifecycle status of an ACTUS event."""

    EXPECTED = "EXPECTED"
    GENERATED = "GENERATED"
    CANCELLED = "CANCELLED"


class ActusEventGenerationStatus(str, Enum):
    """Overall status of ACTUS event generation for a contract."""

    GENERATED = "GENERATED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    UNSUPPORTED = "UNSUPPORTED"
    INVALID = "INVALID"


class ActusEvent(BaseModel):
    """Domain model representing a single expected ACTUS contractual event."""

    event_id: str = Field(..., description="Unique event identifier (UUID v4)")
    contract_id: str = Field(..., description="Associated source contract ID")
    event_type: ActusEventType = Field(..., description="ACTUS event type (e.g., IED, IP, PR, MD)")
    event_time: str = Field(..., description="Scheduled event timestamp in ISO 8601 format (UTC)")
    sequence: int = Field(..., description="Chronological sequence order index (1-based)")
    event_status: ActusEventStatus = Field(default=ActusEventStatus.EXPECTED, description="Event status")
    source_actus_contract_id: str = Field(..., description="Source ACTUS contract ID")

    currency: Optional[str] = Field(default=None, description="Contract currency")
    notional_principal: Optional[Decimal] = Field(default=None, description="Notional principal amount")
    nominal_interest_rate: Optional[Decimal] = Field(default=None, description="Nominal interest rate fraction")
    event_reference: Optional[str] = Field(default=None, description="Human readable event description/reference")

    model_config = ConfigDict(use_enum_values=False)
