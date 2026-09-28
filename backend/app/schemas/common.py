"""Common Pydantic schemas for request and response validation."""

from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    """Schema for root status endpoint response."""

    message: str = Field(..., description="Application status message")
    status: str = Field(..., description="Application execution state")


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str = Field(..., description="Health status indicator")
