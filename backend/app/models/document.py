"""Document domain models and enums."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentStatus(str, Enum):
    """Uploaded document lifecycle status."""

    UPLOADED = "UPLOADED"
    TEXT_EXTRACTED = "TEXT_EXTRACTED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    TEXT_NOT_EXTRACTABLE = "TEXT_NOT_EXTRACTABLE"
    CONFIRMED = "CONFIRMED"


class ConfidenceLevel(str, Enum):
    """Heuristic confidence levels for extracted financial contract terms."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NOT_FOUND = "NOT_FOUND"


class DocumentMetadata(BaseModel):
    """Domain model representing metadata for an uploaded document."""

    document_id: str = Field(..., description="Unique document identifier (UUID v4)")
    original_filename: str = Field(..., description="Original filename uploaded by user")
    content_type: str = Field(..., description="MIME content type of the file")
    file_size: int = Field(..., description="File size in bytes")
    file_path: str = Field(..., description="Local storage file path")
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED, description="Document processing status")
    created_at: datetime = Field(..., description="UTC creation timestamp")
    extracted_text_length: int = Field(default=0, description="Total characters extracted")
    contract_id: Optional[str] = Field(default=None, description="Linked FinancialContract ID once confirmed")

    model_config = ConfigDict(use_enum_values=False)
