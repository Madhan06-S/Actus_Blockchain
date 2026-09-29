"""Service layer managing document uploads, text extraction, term extraction, and confirmation."""

from datetime import datetime, timezone
import os
from pathlib import Path
import threading
from typing import Dict, List, Optional
import uuid

from fastapi import HTTPException, UploadFile, status

from app.models.document import DocumentMetadata, DocumentStatus
from app.repositories.document_repository import DocumentRepository, document_repository
from app.schemas.contract import FinancialContractCreate
from app.schemas.document import (
    DocumentConfirmResponse,
    DocumentStatusResponse,
    DocumentTextResponse,
    DocumentUploadResponse,
    ExtractedTermsResponse,
)
from app.services.contract_service import ContractService, contract_service
from app.services.contract_term_extractor import ContractTermExtractor
from app.services.document_text_extractor import DocumentTextExtractor

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
STORAGE_DIR = Path("storage/documents")


class DocumentService:
    """Business service for handling PDF document lifecycle."""

    def __init__(
        self,
        repository: DocumentRepository = document_repository,
        contract_svc: ContractService = contract_service,
    ) -> None:
        self.repository = repository
        self.contract_service = contract_svc
        self._lock = threading.Lock()
        # Ensure local storage directory exists
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    def upload_document(self, file: UploadFile) -> DocumentUploadResponse:
        """Validate, store, and process an uploaded PDF document.
        
        Validates file existence, filename extension, non-empty content, size <= 10MB,
        and PDF magic bytes header.
        """
        filename = file.filename or ""
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file extension. Only .pdf files are accepted.",
            )

        # Read at most MAX_FILE_SIZE_BYTES + 1 bytes to prevent reading arbitrarily large files into memory
        content = file.file.read(MAX_FILE_SIZE_BYTES + 1)
        file_size = len(content)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size} bytes) exceeds maximum allowed limit of 10 MB.",
            )

        # Verify PDF magic bytes header (%PDF-)
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is not a valid PDF document.",
            )

        # Generate unique document ID
        document_id = str(uuid.uuid4())
        file_path = STORAGE_DIR / f"{document_id}.pdf"

        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(content)

        # Extract text from saved PDF
        extraction_result = DocumentTextExtractor.extract_text_from_file(str(file_path))

        now_utc = datetime.now(timezone.utc)
        doc_metadata = DocumentMetadata(
            document_id=document_id,
            original_filename=filename,
            content_type=file.content_type or "application/pdf",
            file_size=file_size,
            file_path=str(file_path),
            status=extraction_result.status,
            created_at=now_utc,
            extracted_text_length=extraction_result.characters_extracted,
        )

        saved = self.repository.save(doc_metadata)

        return DocumentUploadResponse(
            document_id=saved.document_id,
            original_filename=saved.original_filename,
            file_size=saved.file_size,
            status=saved.status,
            created_at=saved.created_at,
        )

    def get_document_metadata(self, document_id: str) -> DocumentStatusResponse:
        """Fetch document metadata record."""
        doc = self.repository.get_by_id(document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found.",
            )
        return DocumentStatusResponse.model_validate(doc)

    def get_extracted_text(self, document_id: str) -> DocumentTextResponse:
        """Retrieve extracted raw text information for a document."""
        doc = self.repository.get_by_id(document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found.",
            )

        result = DocumentTextExtractor.extract_text_from_file(doc.file_path)
        return DocumentTextResponse(
            document_id=document_id,
            page_count=result.page_count,
            characters_extracted=result.characters_extracted,
            text=result.text,
            status=result.status,
        )

    def get_extracted_terms(self, document_id: str) -> ExtractedTermsResponse:
        """Retrieve candidate financial terms extracted from the PDF."""
        doc = self.repository.get_by_id(document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found.",
            )

        text_result = DocumentTextExtractor.extract_text_from_file(doc.file_path)
        return ContractTermExtractor.extract_terms(text_result.text, document_id)

    def confirm_document(
        self, document_id: str, payload: FinancialContractCreate
    ) -> DocumentConfirmResponse:
        """Confirm user-reviewed financial terms and create a validated FinancialContract.
        
        Reuses Phase 1 ContractService validation. Links document_id to contract_id.
        Raises HTTP 400 if document has already been confirmed.
        """
        with self._lock:
            doc = self.repository.get_by_id(document_id)
            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document with ID '{document_id}' not found.",
                )

            if doc.status == DocumentStatus.CONFIRMED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Document with ID '{document_id}' has already been confirmed and linked to contract '{doc.contract_id}'.",
                )

            previous_status = doc.status
            # Reserve confirmation state to prevent concurrent double creation
            doc.status = DocumentStatus.CONFIRMED
            self.repository.save(doc)

        try:
            # Delegate validation and contract creation to Phase 1 ContractService
            contract_resp = self.contract_service.create_contract(payload)
        except Exception:
            with self._lock:
                doc.status = previous_status
                doc.contract_id = None
                self.repository.save(doc)
            raise

        with self._lock:
            doc.contract_id = contract_resp.contract_id
            doc.status = DocumentStatus.CONFIRMED
            self.repository.save(doc)

        return DocumentConfirmResponse(
            document_id=document_id,
            contract_id=contract_resp.contract_id,
            status="VALIDATED",
            message="Document terms confirmed and financial contract validated.",
        )


# Global default service instance
doc_service = DocumentService()
