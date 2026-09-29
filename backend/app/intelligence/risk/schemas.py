"""Pydantic schemas for AI Risk Prediction service."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FeatureImportanceItem(BaseModel):
    """Metadata item for a feature used in risk prediction."""
    name: str = Field(..., description="Feature variable name")
    value: Any = Field(..., description="Extracted numerical or categorical feature value")
    description: str = Field(..., description="Human-readable description of feature")


class RiskPredictionResponse(BaseModel):
    """Response schema for contract AI risk prediction."""
    contract_id: str = Field(..., description="ID of evaluated contract")
    default_probability: Optional[float] = Field(None, description="Predicted default probability (0.0 to 1.0)")
    default_probability_percent: Optional[float] = Field(None, description="Predicted default probability as percentage (0 to 100%)")
    risk_category: str = Field(..., description="Risk category: LOW, MEDIUM, HIGH, or NOT_AVAILABLE")
    expected_loss: Optional[float] = Field(None, description="Exposure at default * Default probability")
    recommendation: str = Field(..., description="Actionable recommendation: APPROVE, APPROVE WITH CONDITIONS, MANUAL REVIEW, REJECT")
    model_available: bool = Field(..., description="Whether trained ML model file was loaded")
    estimator_type: str = Field("Prototype risk estimator", description="Description of estimator engine used")
    features_used: List[FeatureImportanceItem] = Field(default_factory=list, description="Extracted quantitative features used")
    message: Optional[str] = Field(None, description="Diagnostic message or model status")
