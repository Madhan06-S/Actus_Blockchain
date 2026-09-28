"""In-memory repository for document metadata persistence."""

from typing import Dict, List, Optional
from app.models.document import DocumentMetadata


class DocumentRepository:
    """In-memory storage repository for DocumentMetadata.
    
    Designed to allow replacing with database/cloud storage in future phases cleanly.
    """

    def __init__(self) -> None:
        self._storage: Dict[str, DocumentMetadata] = {}

    def save(self, document: DocumentMetadata) -> DocumentMetadata:
        """Store or update a document metadata record."""
        self._storage[document.document_id] = document
        return document

    def get_by_id(self, document_id: str) -> Optional[DocumentMetadata]:
        """Retrieve document metadata by document ID."""
        return self._storage.get(document_id)

    def get_all(self) -> List[DocumentMetadata]:
        """Retrieve all stored document metadata records."""
        return list(self._storage.values())

    def clear(self) -> None:
        """Clear all stored document metadata (used for testing teardown)."""
        self._storage.clear()


# Global singleton instance
document_repository = DocumentRepository()
