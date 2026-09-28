"""Pydantic schemas for ACTUS Event API request and response models."""

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.actus_event import (
    ActusEventGenerationStatus,
    ActusEventStatus,
    ActusEventType,
)


class ActusEventResponse(BaseModel):
    """Schema representing an individual expected ACTUS contractual event."""

    event_id: str = Field(..., description="Unique event identifier (UUID v4)")
    contract_id: str = Field(..., description="Associated contract ID")
    event_type: ActusEventType = Field(..., description="ACTUS event type (IED, IP, PR, PP, MD)")
    event_time: str = Field(..., description="ISO 8601 UTC event timestamp")
    sequence: int = Field(..., description="1-based sequence order number")
    event_status: ActusEventStatus = Field(..., description="Event status")
    source_actus_contract_id: str = Field(..., description="Source ACTUS contract ID")

    currency: Optional[str] = Field(default=None, description="Contract currency")
    notional_principal: Optional[Decimal] = Field(default=None, description="Notional principal")
    nominal_interest_rate: Optional[Decimal] = Field(default=None, description="Nominal interest rate")
    event_reference: Optional[str] = Field(default=None, description="Event description or reference label")

    model_config = ConfigDict(from_attributes=True)


class ActusEventListResponse(BaseModel):
    """Schema for returning a list of ACTUS events."""

    total: int = Field(..., description="Total event count")
    events: List[ActusEventResponse] = Field(..., description="List of ACTUS events")

    model_config = ConfigDict(from_attributes=True)


class ActusEventGenerationResponse(BaseModel):
    """Schema representing the result of ACTUS event schedule generation."""

    contract_id: str = Field(..., description="Source contract ID")
    actus_contract_type: Optional[str] = Field(default=None, description="ACTUS contract type")
    generation_status: ActusEventGenerationStatus = Field(..., description="Event generation evaluation status")
    total_events: int = Field(..., description="Total generated events count")
    events: List[ActusEventResponse] = Field(default_factory=list, description="Ordered timeline of expected events")
    warnings: List[str] = Field(default_factory=list, description="Generation warnings or notes")
    missing_attributes: List[str] = Field(default_factory=list, description="Missing attributes preventing complete generation")

    model_config = ConfigDict(from_attributes=True)
