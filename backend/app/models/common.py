"""Common domain structures and base types for persistence models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BaseModelEntity(BaseModel):
    """Base model entity structure for domain items, prepared for future persistence."""

    id: Optional[str] = Field(default=None, description="Unique entity identifier")
    created_at: Optional[datetime] = Field(default=None, description="Timestamp when record was created")
    updated_at: Optional[datetime] = Field(default=None, description="Timestamp when record was last updated")
