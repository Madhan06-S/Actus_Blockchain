"""Unit tests verifying fixes for review comments."""

from datetime import datetime, timezone
from decimal import Decimal
import io
import pytest

from app.models.contract import ContractRole, FinancialContract, PaymentFrequency
from app.models.document import DocumentStatus
from app.repositories.contract_repository import contract_repository
from app.repositories.document_repository import document_repository
from app.schemas.contract import FinancialContractCreate
from app.services.actus_mapper import ActusMapper
from app.services.contract_term_extractor import ContractTermExtractor, normalize_date_string
from app.services.document_service import DocumentService


@pytest.fixture(autouse=True)
def clear_all_repos() -> None:
    document_repository.clear()
    contract_repository.clear()
    yield
    document_repository.clear()
    contract_repository.clear()


def test_actus_mapper_lam_before_ann() -> None:
    """Verify linear amortizing loan is classified as LAM, not ANN."""
    contract = FinancialContract(
        contract_id="c-lam-1",
        principal=Decimal("100000"),
        currency="USD",
        annual_interest_rate=Decimal("5.0"),
        start_date="2027-01-01",
        maturity_date="2030-01-01",
        payment_frequency=PaymentFrequency.MONTHLY,
        contract_role=ContractRole.RPA,
        description="Linear amortizing loan with equal principal payments",
        created_at=datetime.now(timezone.utc),
    )
    rec = ActusMapper.map_contract(contract)
    assert rec.mapping_status.value == "MAPPED"
    assert rec.actus_contract.contractType == "LAM"


def test_actus_mapper_negative_amortization_guard() -> None:
    """Verify non-amortizing loan returns REQUIRES_REVIEW instead of matching ANN."""
    contract = FinancialContract(
        contract_id="c-neg-1",
        principal=Decimal("100000"),
        currency="USD",
        annual_interest_rate=Decimal("5.0"),
        start_date="2027-01-01",
        maturity_date="2030-01-01",
        payment_frequency=PaymentFrequency.MONTHLY,
        contract_role=ContractRole.RPA,
        description="Non-amortizing loan structure requiring custom schedule",
        created_at=datetime.now(timezone.utc),
    )
    rec = ActusMapper.map_contract(contract)
    assert rec.mapping_status.value == "REQUIRES_REVIEW"
    assert rec.actus_contract.contractType is None


def test_actus_mapper_word_boundary() -> None:
    """Verify substring matches like 'laminate' do not match LAM."""
    contract = FinancialContract(
        contract_id="c-wb-1",
        principal=Decimal("100000"),
        currency="USD",
        annual_interest_rate=Decimal("5.0"),
        start_date="2027-01-01",
        maturity_date="2030-01-01",
        payment_frequency=PaymentFrequency.MONTHLY,
        contract_role=ContractRole.RPA,
        description="Laminate coating supply financing agreement",
        created_at=datetime.now(timezone.utc),
    )
    rec = ActusMapper.map_contract(contract)
    assert rec.mapping_status.value == "REQUIRES_REVIEW"
    assert rec.actus_contract.contractType is None


def test_date_ambiguity_returns_none() -> None:
    """Verify date parsing returns None for ambiguous date strings like 03/04/2027."""
    assert normalize_date_string("03/04/2027") is None
    assert normalize_date_string("01/01/2027") == "2027-01-01"
    assert normalize_date_string("01/15/2027") == "2027-01-15"
    assert normalize_date_string("2027-05-10") == "2027-05-10"


def test_currency_black_square_not_detected_as_inr() -> None:
    """Verify black square glyph \\u25a0 does not trigger INR currency detection."""
    val, conf, src = ContractTermExtractor._extract_currency("Total payment \u25a0 100000")
    assert val is None


def test_confirm_document_concurrency_guard() -> None:
    """Verify confirm_document prevents double confirmation using state reservation."""
    doc_service = DocumentService()
    # Create mock metadata
    from app.models.document import DocumentMetadata
    doc_meta = DocumentMetadata(
        document_id="doc-test-lock",
        original_filename="test.pdf",
        content_type="application/pdf",
        file_size=1000,
        file_path="storage/documents/test.pdf",
        status=DocumentStatus.TEXT_EXTRACTED,
        created_at=datetime.now(timezone.utc),
    )
    document_repository.save(doc_meta)

    payload = FinancialContractCreate(
        principal=Decimal("100000"),
        currency="INR",
        annual_interest_rate=Decimal("10.0"),
        start_date="2027-01-01",
        maturity_date="2029-01-01",
        payment_frequency=PaymentFrequency.MONTHLY,
        contract_role=ContractRole.RPA,
        description="Test confirmation",
    )

    resp = doc_service.confirm_document("doc-test-lock", payload)
    assert resp.status == "VALIDATED"

    # Second confirm call should fail with 400 BAD_REQUEST
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        doc_service.confirm_document("doc-test-lock", payload)
    assert exc_info.value.status_code == 400
