"""Pydantic schemas for Negotiation Agent service."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProposedTerm(BaseModel):
    """Specific term adjustment suggestion."""
    parameter: str = Field(..., description="Target parameter (e.g. interest_rate, tenure)")
    current_value: str = Field(..., description="Current contractual value")
    proposed_value: str = Field(..., description="Proposed restructured value")
    reason: str = Field(..., description="Rationale for proposed adjustment")


class NegotiationRequest(BaseModel):
    """Request schema for contract term negotiation proposal."""
    objective: Optional[str] = Field("Reduce lender risk while maintaining realistic borrower terms", description="User negotiation objective")


class NegotiationResponse(BaseModel):
    """Response schema for negotiation proposal."""
    contract_id: str
    available: bool = Field(True, description="Whether Groq or negotiation engine is available")
    optimized_terms: List[ProposedTerm] = Field(default_factory=list)
    negotiation_summary: str = Field("", description="Executive summary of proposal")
    revised_actus_json: Dict[str, Any] = Field(default_factory=dict, description="Proposed ACTUS representation (marked PROPOSED)")
    requires_human_approval: bool = Field(True, description="Always true; requires explicit human approval")
    message: Optional[str] = Field(None, description="Diagnostic or availability message")
