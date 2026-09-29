"""Pydantic schemas for Scenario Stress Testing."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class StressTestRequest(BaseModel):
    """Request schema for contract stress testing."""
    rate_shock_percent: float = Field(3.0, description="Interest rate shock percentage points to add (e.g. 3.0 for +3%)")
    scenario_description: Optional[str] = Field("Interest rate increase by +3.0%", description="User scenario description")


class StressCaseDetails(BaseModel):
    """Details for base or stressed financial case."""
    annual_interest_rate: float
    monthly_payment: float
    total_interest: float
    total_repayment: float
    default_probability: Optional[float] = None
    risk_category: str = "LOW"


class StressDifferenceDetails(BaseModel):
    """Variance metrics between base case and stressed case."""
    rate_shock_percent: float
    additional_monthly_payment: float
    additional_interest: float
    additional_total_repayment: float
    percentage_increase_in_interest: float


class StressTestResponse(BaseModel):
    """Response schema for scenario stress test."""
    contract_id: str
    scenario_description: str
    base_case: StressCaseDetails
    stressed_case: StressCaseDetails
    difference: StressDifferenceDetails
    risk_impact: Dict[str, Any]
