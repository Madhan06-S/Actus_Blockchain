"""Pydantic schemas for Document API endpoints."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import ConfidenceLevel, DocumentStatus
from app.schemas.contract import FinancialContractCreate


class DocumentUploadResponse(BaseModel):
    """Response returned upon uploading a document."""

    document_id: str = Field(..., description="Unique document identifier (UUID v4)")
    original_filename: str = Field(..., description="Uploaded file name")
    file_size: int = Field(..., description="File size in bytes")
    status: DocumentStatus = Field(..., description="Document processing status")
    created_at: datetime = Field(..., description="UTC upload timestamp")

    model_config = ConfigDict(from_attributes=True)


class DocumentStatusResponse(BaseModel):
    """Response returned when fetching document status metadata."""

    document_id: str = Field(..., description="Unique document identifier (UUID v4)")
    original_filename: str = Field(..., description="Uploaded file name")
    content_type: str = Field(..., description="MIME content type")
    file_size: int = Field(..., description="File size in bytes")
    status: DocumentStatus = Field(..., description="Document status")
    created_at: datetime = Field(..., description="UTC creation timestamp")
    extracted_text_length: int = Field(..., description="Character count extracted")
    contract_id: Optional[str] = Field(default=None, description="Linked contract ID if confirmed")

    model_config = ConfigDict(from_attributes=True)


class DocumentTextResponse(BaseModel):
    """Response returned when retrieving extracted PDF text."""

    document_id: str = Field(..., description="Unique document identifier (UUID v4)")
    page_count: int = Field(..., description="Total pages in PDF")
    characters_extracted: int = Field(..., description="Total characters extracted")
    text: str = Field(..., description="Full extracted document text")
    status: DocumentStatus = Field(..., description="Extraction status")


class FieldExtractionResult(BaseModel):
    """Single extracted financial term with confidence indicator and text snippet."""

    value: Optional[str] = Field(default=None, description="Extracted candidate value")
    confidence: ConfidenceLevel = Field(..., description="Heuristic confidence rating")
    source: Optional[str] = Field(default=None, description="Short relevant text snippet source")


class ExtractedTermsResponse(BaseModel):
    """Response returned when retrieving candidate financial contract terms."""

    document_id: str = Field(..., description="Unique document identifier (UUID v4)")
    status: DocumentStatus = Field(..., description="Document processing status")
    fields: Dict[str, FieldExtractionResult] = Field(..., description="Map of extracted candidate terms")
    missing_fields: List[str] = Field(..., description="List of required contract terms that were missing")
    warnings: List[str] = Field(..., description="List of extraction warnings or notes")


class DocumentConfirmRequest(FinancialContractCreate):
    """Request schema for confirming or correcting extracted terms.
    
    Reuses Phase 1 FinancialContractCreate schema directly to ensure zero duplication of validation rules.
    """

    pass


class DocumentConfirmResponse(BaseModel):
    """Response schema returned upon successfully confirming document terms."""

    document_id: str = Field(..., description="Unique document ID")
    contract_id: str = Field(..., description="Newly created FinancialContract ID")
    status: str = Field(default="VALIDATED", description="Contract status")
    message: str = Field(..., description="Confirmation result summary message")
