"""Comprehensive tests for PDF document upload, text extraction, term extraction, and confirmation."""

import io
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.main import app
from app.repositories.contract_repository import contract_repository
from app.repositories.document_repository import document_repository

client = TestClient(app)


def create_sample_pdf_bytes(lines: list[str]) -> bytes:
    """Helper to generate a valid text-based PDF in memory."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    for line in lines:
        c.drawString(100, y, line)
        y -= 25
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


def create_image_only_pdf_bytes() -> bytes:
    """Helper to generate a PDF with graphics/shapes but zero text strings."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.rect(100, 100, 400, 400, fill=1)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


@pytest.fixture(autouse=True)
def clear_repos() -> None:
    """Clear document and contract repositories before and after each test."""
    document_repository.clear()
    contract_repository.clear()
    yield
    document_repository.clear()
    contract_repository.clear()


# ============================================================================
# UPLOAD TESTS
# ============================================================================

def test_1_valid_pdf_upload_succeeds() -> None:
    """Test 1: Valid PDF upload returns 201 Created and document metadata."""
    pdf_bytes = create_sample_pdf_bytes(["Test Loan Agreement", "Principal amount: ₹100,000"])
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("loan_agreement.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 201
    data = response.json()
    assert "document_id" in data
    assert data["original_filename"] == "loan_agreement.pdf"
    assert data["file_size"] > 0
    assert data["status"] == "TEXT_EXTRACTED"


def test_2_non_pdf_extension_rejected() -> None:
    """Test 2: Reject non-PDF file extension."""
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("contract.docx", b"some content", "application/vnd.openxmlformats-officedocument")},
    )
    assert response.status_code == 400
    assert "Invalid file extension" in response.json()["detail"]


def test_3_oversized_file_rejected() -> None:
    """Test 3: Reject PDF exceeding 10 MB limit."""
    large_bytes = b"%PDF-1.4\n" + b"X" * (10 * 1024 * 1024 + 100)
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("huge.pdf", large_bytes, "application/pdf")},
    )
    assert response.status_code == 400
    assert "exceeds maximum allowed limit" in response.json()["detail"]


def test_4_empty_file_rejected() -> None:
    """Test 4: Reject empty PDF file (0 bytes)."""
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert "Uploaded file is empty" in response.json()["detail"]


def test_5_corrupt_pdf_rejected() -> None:
    """Test 5: Reject invalid/corrupt file content (missing %PDF- header)."""
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("corrupt.pdf", b"NOT A PDF CONTENT", "application/pdf")},
    )
    assert response.status_code == 400
    assert "not a valid PDF document" in response.json()["detail"]


def test_6_document_receives_uuid() -> None:
    """Test 6: Document receives a valid UUID v4 identifier."""
    pdf_bytes = create_sample_pdf_bytes(["Sample content"])
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = response.json()["document_id"]
    assert len(doc_id) == 36


def test_7_document_metadata_stored() -> None:
    """Test 7: Document metadata is stored and retrievable via GET /api/v1/documents/{id}."""
    pdf_bytes = create_sample_pdf_bytes(["Sample content"])
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload_resp.json()["document_id"]

    get_resp = client.get(f"/api/v1/documents/{doc_id}")
    assert get_resp.status_code == 200
    meta = get_resp.json()
    assert meta["document_id"] == doc_id
    assert meta["original_filename"] == "test.pdf"


# ============================================================================
# TEXT EXTRACTION TESTS
# ============================================================================

def test_8_pdf_text_extraction() -> None:
    """Test 8: Extract text from text-based PDF fixture."""
    lines = [
        "Principal amount: INR 100,000",
        "Annual interest rate: 10%",
        "Start date: January 1, 2027",
        "Maturity date: January 1, 2029",
        "Payments are monthly.",
    ]
    pdf_bytes = create_sample_pdf_bytes(lines)
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("loan.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload_resp.json()["document_id"]

    text_resp = client.get(f"/api/v1/documents/{doc_id}/text")
    assert text_resp.status_code == 200
    data = text_resp.json()
    assert data["page_count"] == 1
    assert data["characters_extracted"] > 0
    assert "Principal amount" in data["text"]
    assert "January 1, 2027" in data["text"]


# ============================================================================
# TERM EXTRACTION TESTS
# ============================================================================

def test_9_term_extraction_standard() -> None:
    """Test 9: Extract candidate financial terms from document text."""
    lines = [
        "Principal amount: INR 100,000",
        "Annual interest rate: 10%",
        "Start date: January 1, 2027",
        "Maturity date: January 1, 2029",
        "Payments shall be made monthly.",
    ]
    pdf_bytes = create_sample_pdf_bytes(lines)
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("loan.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload_resp.json()["document_id"]

    terms_resp = client.get(f"/api/v1/documents/{doc_id}/terms")
    assert terms_resp.status_code == 200
    data = terms_resp.json()
    fields = data["fields"]

    assert fields["principal"]["value"] == "100000"
    assert fields["currency"]["value"] == "INR"
    assert fields["annual_interest_rate"]["value"] == "10"
    assert fields["start_date"]["value"] == "2027-01-01"
    assert fields["maturity_date"]["value"] == "2029-01-01"
    assert fields["payment_frequency"]["value"] == "MONTHLY"
    assert len(data["missing_fields"]) == 0


def test_10_term_extraction_various_text_formats() -> None:
    """Test 10: Extract terms using alternative text formatting."""
    lines = [
        "Loan amount of Rs. 100,000",
        "10 percent annual interest",
        "Commencement date: 2027-01-01",
        "Maturity date: 2029-01-01",
        "Paid monthly",
    ]
    pdf_bytes = create_sample_pdf_bytes(lines)
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("loan_alt.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload_resp.json()["document_id"]

    terms_resp = client.get(f"/api/v1/documents/{doc_id}/terms")
    assert terms_resp.status_code == 200
    fields = terms_resp.json()["fields"]

    assert fields["principal"]["value"] == "100000"
    assert fields["currency"]["value"] == "INR"
    assert fields["annual_interest_rate"]["value"] == "10"
    assert fields["start_date"]["value"] == "2027-01-01"
    assert fields["maturity_date"]["value"] == "2029-01-01"
    assert fields["payment_frequency"]["value"] == "MONTHLY"


# ============================================================================
# MISSING FIELD TEST
# ============================================================================

def test_11_missing_field_detection() -> None:
    """Test 11: Missing maturity_date appears in missing_fields without guessing."""
    lines = [
        "Principal amount: INR 100,000",
        "Annual interest rate: 10%",
        "Start date: January 1, 2027",
        "Payments are monthly.",
    ]
    pdf_bytes = create_sample_pdf_bytes(lines)
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("missing_maturity.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload_resp.json()["document_id"]

    terms_resp = client.get(f"/api/v1/documents/{doc_id}/terms")
    data = terms_resp.json()
    assert "maturity_date" in data["missing_fields"]
    assert data["fields"]["maturity_date"]["value"] is None


# ============================================================================
# SCANNED PDF TEST
# ============================================================================

def test_12_scanned_pdf_returns_text_not_extractable() -> None:
    """Test 12: Image-only/scanned PDF returns TEXT_NOT_EXTRACTABLE."""
    pdf_bytes = create_image_only_pdf_bytes()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("scanned.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_resp.status_code == 201
    assert upload_resp.json()["status"] == "TEXT_NOT_EXTRACTABLE"

    doc_id = upload_resp.json()["document_id"]
    text_resp = client.get(f"/api/v1/documents/{doc_id}/text")
    assert text_resp.json()["characters_extracted"] == 0
    assert text_resp.json()["status"] == "TEXT_NOT_EXTRACTABLE"


# ============================================================================
# CONFIRMATION TESTS
# ============================================================================

CONFIRM_PAYLOAD = {
    "principal": 100000,
    "currency": "INR",
    "annual_interest_rate": 10.0,
    "start_date": "2027-01-01",
    "maturity_date": "2029-01-01",
    "payment_frequency": "MONTHLY",
    "contract_role": "RPA",
    "description": "Confirmed contract from PDF upload",
}


def test_13_confirm_extracted_terms_succeeds() -> None:
    """Test 13: Confirming valid terms creates FinancialContract and returns contract_id."""
    pdf_bytes = create_sample_pdf_bytes(["Loan terms"])
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload_resp.json()["document_id"]

    confirm_resp = client.post(f"/api/v1/documents/{doc_id}/confirm", json=CONFIRM_PAYLOAD)
    assert confirm_resp.status_code == 200
    data = confirm_resp.json()
    assert data["document_id"] == doc_id
    assert "contract_id" in data
    assert data["status"] == "VALIDATED"


def test_14_user_correction_during_confirmation() -> None:
    """Test 14: User corrects an extracted term and confirmation succeeds."""
    pdf_bytes = create_sample_pdf_bytes(["Principal: 50000"])
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload_resp.json()["document_id"]

    # User corrects principal from 50000 to 100000
    corrected_payload = {**CONFIRM_PAYLOAD, "principal": 100000}
    confirm_resp = client.post(f"/api/v1/documents/{doc_id}/confirm", json=corrected_payload)
    assert confirm_resp.status_code == 200
    contract_id = confirm_resp.json()["contract_id"]

    # Verify updated contract details via Phase 1 endpoint
    contract_resp = client.get(f"/api/v1/contracts/{contract_id}")
    assert contract_resp.status_code == 200
    assert Decimal(str(contract_resp.json()["principal"])) == Decimal("100000")


def test_15_invalid_confirmed_terms_rejected_by_phase1() -> None:
    """Test 15: Invalid confirmed terms (principal <= 0) rejected by Phase 1 validation."""
    pdf_bytes = create_sample_pdf_bytes(["Test content"])
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload_resp.json()["document_id"]

    invalid_payload = {**CONFIRM_PAYLOAD, "principal": -500}
    confirm_resp = client.post(f"/api/v1/documents/{doc_id}/confirm", json=invalid_payload)
    assert confirm_resp.status_code == 422


def test_16_missing_required_confirmed_terms_rejected() -> None:
    """Test 16: Missing required confirmed terms rejected by schema validation."""
    pdf_bytes = create_sample_pdf_bytes(["Test content"])
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload_resp.json()["document_id"]

    incomplete_payload = {k: v for k, v in CONFIRM_PAYLOAD.items() if k != "principal"}
    confirm_resp = client.post(f"/api/v1/documents/{doc_id}/confirm", json=incomplete_payload)
    assert confirm_resp.status_code == 422


def test_17_unknown_document_id_returns_404() -> None:
    """Test 17: Unknown document ID on confirm returns 404."""
    confirm_resp = client.post("/api/v1/documents/non-existent-doc-id/confirm", json=CONFIRM_PAYLOAD)
    assert confirm_resp.status_code == 404


def test_18_confirming_already_confirmed_document_fails() -> None:
    """Test 18: Confirming an already confirmed document fails with HTTP 400."""
    pdf_bytes = create_sample_pdf_bytes(["Test content"])
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload_resp.json()["document_id"]

    # First confirmation
    client.post(f"/api/v1/documents/{doc_id}/confirm", json=CONFIRM_PAYLOAD)

    # Second confirmation attempt
    second_confirm = client.post(f"/api/v1/documents/{doc_id}/confirm", json=CONFIRM_PAYLOAD)
    assert second_confirm.status_code == 400
    assert "already been confirmed" in second_confirm.json()["detail"]


def test_19_contract_retrievable_via_phase1_endpoint() -> None:
    """Test 19: Contract created via document confirmation is retrievable via GET /api/v1/contracts/{id}."""
    pdf_bytes = create_sample_pdf_bytes(["Test content"])
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload_resp.json()["document_id"]

    confirm_resp = client.post(f"/api/v1/documents/{doc_id}/confirm", json=CONFIRM_PAYLOAD)
    contract_id = confirm_resp.json()["contract_id"]

    get_resp = client.get(f"/api/v1/contracts/{contract_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["contract_id"] == contract_id
    assert data["currency"] == "INR"
    assert data["status"] == "VALIDATED"
