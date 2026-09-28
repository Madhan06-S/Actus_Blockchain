"""Service for extracting text content from PDF files using pypdf."""

from typing import Optional
from pydantic import BaseModel
import pypdf

from app.models.document import DocumentStatus


class PDFTextExtractionResult(BaseModel):
    """Result structure from PDF text extraction."""

    text: str
    page_count: int
    characters_extracted: int
    status: DocumentStatus
    error_message: Optional[str] = None


class DocumentTextExtractor:
    """Service class for deterministic PDF text extraction."""

    @staticmethod
    def extract_text_from_file(file_path: str) -> PDFTextExtractionResult:
        """Read a PDF file from disk and extract page text.
        
        Preserves page boundaries and detects whether extractable text exists.
        Handles corrupt or unreadable PDFs gracefully.
        """
        try:
            reader = pypdf.PdfReader(file_path)
            page_count = len(reader.pages)
            extracted_pages = []

            for page in reader.pages:
                page_text = page.extract_text() or ""
                extracted_pages.append(page_text.strip())

            full_text = "\n\n".join(p for p in extracted_pages if p)
            characters_extracted = len(full_text)

            if characters_extracted == 0 or not full_text.strip():
                return PDFTextExtractionResult(
                    text="",
                    page_count=page_count,
                    characters_extracted=0,
                    status=DocumentStatus.TEXT_NOT_EXTRACTABLE,
                    error_message="No extractable text found in PDF. Scanned images/OCR are not supported in Phase 2.",
                )

            return PDFTextExtractionResult(
                text=full_text,
                page_count=page_count,
                characters_extracted=characters_extracted,
                status=DocumentStatus.TEXT_EXTRACTED,
            )
        except Exception as exc:
            return PDFTextExtractionResult(
                text="",
                page_count=0,
                characters_extracted=0,
                status=DocumentStatus.EXTRACTION_FAILED,
                error_message=f"Failed to parse PDF document: {str(exc)}",
            )
