"""API routes for Document Upload, Text Extraction, and Term Confirmation."""

from fastapi import APIRouter, File, status, UploadFile

from app.schemas.document import (
    DocumentConfirmRequest,
    DocumentConfirmResponse,
    DocumentStatusResponse,
    DocumentTextResponse,
    DocumentUploadResponse,
    ExtractedTermsResponse,
)
from app.services.document_service import doc_service

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF financial contract document",
)
def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    """Upload a PDF contract document (max size: 10 MB).
    
    Validates file extension, magic bytes, and performs automatic text extraction.
    """
    return doc_service.upload_document(file)


@router.get(
    "/{document_id}",
    response_model=DocumentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve document metadata and status",
)
def get_document_status(document_id: str) -> DocumentStatusResponse:
    """Retrieve processing status and metadata for an uploaded document."""
    return doc_service.get_document_metadata(document_id)


@router.get(
    "/{document_id}/text",
    response_model=DocumentTextResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve extracted text from PDF document",
)
def get_document_text(document_id: str) -> DocumentTextResponse:
    """Retrieve full text extracted from an uploaded PDF document."""
    return doc_service.get_extracted_text(document_id)


@router.post(
    "/{document_id}/extract",
    response_model=ExtractedTermsResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger extraction of candidate financial terms",
)
def extract_document_terms(document_id: str) -> ExtractedTermsResponse:
    """Extract candidate financial contract terms from document text."""
    return doc_service.get_extracted_terms(document_id)


@router.get(
    "/{document_id}/terms",
    response_model=ExtractedTermsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve extracted candidate financial terms",
)
def get_document_terms(document_id: str) -> ExtractedTermsResponse:
    """Retrieve candidate financial terms extracted from an uploaded PDF document."""
    return doc_service.get_extracted_terms(document_id)


@router.post(
    "/{document_id}/confirm",
    response_model=DocumentConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm or correct extracted terms and create a validated FinancialContract",
)
def confirm_document_terms(
    document_id: str, payload: DocumentConfirmRequest
) -> DocumentConfirmResponse:
    """Confirm user-reviewed financial terms.
    
    Reuses Phase 1 validation rules to create and store a validated FinancialContract.
    """
    return doc_service.confirm_document(document_id, payload)
