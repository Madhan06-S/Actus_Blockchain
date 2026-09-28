"""Comprehensive test suite for Phase 6 Contract Hashing and Integrity Verification."""

from datetime import date, datetime, timezone
from decimal import Decimal
import uuid
from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.models.actus import ActusContract
from app.models.contract import ContractRole, ContractStatus, FinancialContract, PaymentFrequency
from app.repositories.actus_repository import actus_repository
from app.repositories.contract_hash_repository import contract_hash_repository
from app.repositories.contract_repository import contract_repository
from app.services.contract_canonicalizer import ContractCanonicalizer
from app.services.contract_hasher import ContractHasher

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_repositories():
    """Clear repositories before each test."""
    contract_repository.clear()
    actus_repository.clear()
    contract_hash_repository.clear()
    yield
    contract_repository.clear()
    actus_repository.clear()
    contract_hash_repository.clear()


def create_sample_contract(
    contract_id: str = "0623b314-e753-49b9-830f-40a97cc0bde1",
    principal: Decimal = Decimal("100000.00"),
    annual_interest_rate: Decimal = Decimal("10.00"),
    currency: str = "INR",
    start_date: date = date(2027, 1, 1),
    maturity_date: date = date(2029, 1, 1),
    payment_frequency: PaymentFrequency = PaymentFrequency.MONTHLY,
    contract_role: ContractRole = ContractRole.RPA,
    created_at: datetime = None,
) -> FinancialContract:
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    contract = FinancialContract(
        contract_id=contract_id,
        principal=principal,
        currency=currency,
        annual_interest_rate=annual_interest_rate,
        start_date=start_date,
        maturity_date=maturity_date,
        payment_frequency=payment_frequency,
        contract_role=contract_role,
        description="Fixed-rate amortizing loan",
        status=ContractStatus.VALIDATED,
        created_at=created_at,
    )
    contract_repository.save(contract)
    return contract


def create_sample_actus_contract(
    contract_id: str = "0623b314-e753-49b9-830f-40a97cc0bde1",
    contract_type: str = "ANN",
    contract_role: str = "RPA",
    nominal_interest_rate: Decimal = Decimal("0.10"),
    cycle_of_interest: str = "P1M",
) -> ActusContract:
    actus = ActusContract(
        contractID=contract_id,
        contractType=contract_type,
        contractRole=contract_role,
        currency="INR",
        notionalPrincipal=Decimal("100000.00"),
        nominalInterestRate=nominal_interest_rate,
        initialExchangeDate="2027-01-01T00:00:00Z",
        maturityDate="2029-01-01T00:00:00Z",
        statusDate="2027-01-01T00:00:00Z",
        cycleOfInterestPayment=cycle_of_interest,
        cycleAnchorDateOfInterestPayment="2027-01-01T00:00:00Z",
        cycleOfPrincipalRedemption=cycle_of_interest if contract_type in ["ANN", "LAM"] else None,
        cycleAnchorDateOfPrincipalRedemption="2027-01-01T00:00:00Z" if contract_type in ["ANN", "LAM"] else None,
        dayCountConvention="30E360",
    )
    from app.models.actus import ActusMappingRecord, ActusMappingStatus
    record = ActusMappingRecord(
        source_contract_id=contract_id,
        mapping_status=ActusMappingStatus.MAPPED,
        actus_contract=actus,
        created_at=datetime.now(timezone.utc),
    )
    actus_repository.save(record)
    return actus


# 1. Same contract produces same hash
def test_same_contract_produces_same_hash():
    fc = create_sample_contract()
    ac = create_sample_actus_contract()
    payload1 = ContractCanonicalizer.build_canonical_payload(fc, ac)
    payload2 = ContractCanonicalizer.build_canonical_payload(fc, ac)
    hash1 = ContractHasher.calculate_hash(payload1)
    hash2 = ContractHasher.calculate_hash(payload2)
    assert hash1 == hash2


# 2. Repeated hashing produces identical result
def test_repeated_hashing_identical():
    fc = create_sample_contract()
    ac = create_sample_actus_contract()
    payload = ContractCanonicalizer.build_canonical_payload(fc, ac)
    hashes = [ContractHasher.calculate_hash(payload) for _ in range(10)]
    assert len(set(hashes)) == 1


# 3. Changing principal changes hash
def test_changing_principal_changes_hash():
    fc1 = create_sample_contract(principal=Decimal("100000.00"))
    ac1 = create_sample_actus_contract()
    hash1 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc1, ac1))

    fc2 = create_sample_contract(principal=Decimal("100001.00"))
    hash2 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc2, ac1))
    assert hash1 != hash2


# 4. Changing interest rate changes hash
def test_changing_interest_rate_changes_hash():
    fc1 = create_sample_contract(annual_interest_rate=Decimal("10.00"))
    ac1 = create_sample_actus_contract()
    hash1 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc1, ac1))

    fc2 = create_sample_contract(annual_interest_rate=Decimal("10.01"))
    hash2 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc2, ac1))
    assert hash1 != hash2


# 5. Changing currency changes hash
def test_changing_currency_changes_hash():
    fc1 = create_sample_contract(currency="INR")
    ac1 = create_sample_actus_contract()
    hash1 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc1, ac1))

    fc2 = create_sample_contract(currency="USD")
    hash2 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc2, ac1))
    assert hash1 != hash2


# 6. Changing start date changes hash
def test_changing_start_date_changes_hash():
    fc1 = create_sample_contract(start_date=date(2027, 1, 1))
    ac1 = create_sample_actus_contract()
    hash1 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc1, ac1))

    fc2 = create_sample_contract(start_date=date(2027, 1, 2))
    hash2 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc2, ac1))
    assert hash1 != hash2


# 7. Changing maturity date changes hash
def test_changing_maturity_date_changes_hash():
    fc1 = create_sample_contract(maturity_date=date(2029, 1, 1))
    ac1 = create_sample_actus_contract()
    hash1 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc1, ac1))

    fc2 = create_sample_contract(maturity_date=date(2029, 1, 2))
    hash2 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc2, ac1))
    assert hash1 != hash2


# 8. Changing payment frequency changes hash
def test_changing_payment_frequency_changes_hash():
    fc1 = create_sample_contract()
    ac1 = create_sample_actus_contract()
    hash1 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc1, ac1))

    # Construct different frequency
    fc2 = create_sample_contract()
    fc2.payment_frequency = "ANNUALLY"
    hash2 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc2, ac1))
    assert hash1 != hash2


# 9. Changing contract role changes hash
def test_changing_contract_role_changes_hash():
    fc1 = create_sample_contract(contract_role=ContractRole.RPA)
    ac1 = create_sample_actus_contract()
    hash1 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc1, ac1))

    fc2 = create_sample_contract(contract_role=ContractRole.RPL)
    hash2 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc2, ac1))
    assert hash1 != hash2


# 10. Changing ACTUS contract type changes hash
def test_changing_actus_contract_type_changes_hash():
    fc = create_sample_contract()
    ac1 = create_sample_actus_contract(contract_type="ANN")
    ac2 = create_sample_actus_contract(contract_type="PAM")
    hash1 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc, ac1))
    hash2 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc, ac2))
    assert hash1 != hash2


# 11. Changing ACTUS interest rate changes hash
def test_changing_actus_interest_rate_changes_hash():
    fc = create_sample_contract()
    ac1 = create_sample_actus_contract(nominal_interest_rate=Decimal("0.10"))
    ac2 = create_sample_actus_contract(nominal_interest_rate=Decimal("0.11"))
    hash1 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc, ac1))
    hash2 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc, ac2))
    assert hash1 != hash2


# 12. Changing ACTUS cycle changes hash
def test_changing_actus_cycle_changes_hash():
    fc = create_sample_contract()
    ac1 = create_sample_actus_contract(cycle_of_interest="P1M")
    ac2 = create_sample_actus_contract(cycle_of_interest="P3M")
    hash1 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc, ac1))
    hash2 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc, ac2))
    assert hash1 != hash2


# 13. Runtime created_at does NOT change hash
def test_runtime_created_at_does_not_change_hash():
    t1 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 28, 23, 50, 0, tzinfo=timezone.utc)
    fc1 = create_sample_contract(created_at=t1)
    fc2 = create_sample_contract(created_at=t2)
    ac = create_sample_actus_contract()

    hash1 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc1, ac))
    hash2 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc2, ac))
    assert hash1 == hash2


# 14. Dictionary key ordering does NOT change hash
def test_dictionary_key_ordering_does_not_change_hash():
    dict_a = {"principal": "100000.00", "currency": "INR", "rate": "10.00"}
    dict_b = {"rate": "10.00", "currency": "INR", "principal": "100000.00"}
    bytes_a = ContractCanonicalizer.to_canonical_bytes(dict_a)
    bytes_b = ContractCanonicalizer.to_canonical_bytes(dict_b)
    hash_a = ContractHasher.calculate_hash(dict_a)
    hash_b = ContractHasher.calculate_hash(dict_b)
    assert bytes_a == bytes_b
    assert hash_a == hash_b


# 15. Decimal formatting differences representing same value do NOT change hash
def test_decimal_formatting_normalization():
    fc1 = create_sample_contract(principal=Decimal("100000"))
    fc2 = create_sample_contract(principal=Decimal("100000.0"))
    fc3 = create_sample_contract(principal=Decimal("100000.00"))
    ac = create_sample_actus_contract()

    h1 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc1, ac))
    h2 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc2, ac))
    h3 = ContractHasher.calculate_hash(ContractCanonicalizer.build_canonical_payload(fc3, ac))
    assert h1 == h2 == h3


# 16. SHA-256 output format is exactly 64 lowercase hexadecimal characters
def test_sha256_output_format():
    fc = create_sample_contract()
    ac = create_sample_actus_contract()
    payload = ContractCanonicalizer.build_canonical_payload(fc, ac)
    digest = ContractHasher.calculate_hash(payload)
    assert len(digest) == 64
    assert digest == digest.lower()
    assert all(c in "0123456789abcdef" for c in digest)


# 17. API POST /hash generates hash successfully
def test_api_generate_contract_hash():
    fc = create_sample_contract()
    ac = create_sample_actus_contract()
    cid = fc.contract_id

    response = client.post(f"/api/v1/contracts/{cid}/hash")
    assert response.status_code == 200
    data = response.json()
    assert data["contract_id"] == cid
    assert data["hash_algorithm"] == "SHA-256"
    assert data["canonical_payload_version"] == "v1"
    assert len(data["contract_hash"]) == 64
    assert "financial_contract" in data["canonical_payload"]


# 18. API GET /hash retrieves stored hash
def test_api_get_contract_hash():
    fc = create_sample_contract()
    ac = create_sample_actus_contract()
    cid = fc.contract_id

    # Post first
    post_res = client.post(f"/api/v1/contracts/{cid}/hash")
    assert post_res.status_code == 200

    # Get
    get_res = client.get(f"/api/v1/contracts/{cid}/hash")
    assert get_res.status_code == 200
    assert get_res.json() == post_res.json()


# 19. API POST /hash/verify returns matches=True when unchanged
def test_api_verify_contract_hash_matches():
    fc = create_sample_contract()
    ac = create_sample_actus_contract()
    cid = fc.contract_id

    client.post(f"/api/v1/contracts/{cid}/hash")
    verify_res = client.post(f"/api/v1/contracts/{cid}/hash/verify")
    assert verify_res.status_code == 200
    vdata = verify_res.json()
    assert vdata["matches"] is True
    assert vdata["expected_hash"] == vdata["calculated_hash"]


# 20. API POST /hash/verify returns matches=False when contractual term changes
def test_api_verify_contract_hash_mismatch():
    fc = create_sample_contract()
    ac = create_sample_actus_contract()
    cid = fc.contract_id

    # Generate initial hash
    client.post(f"/api/v1/contracts/{cid}/hash")

    # Modify underlying contract term in repository
    fc.annual_interest_rate = Decimal("11.00")
    contract_repository.save(fc)

    verify_res = client.post(f"/api/v1/contracts/{cid}/hash/verify")
    assert verify_res.status_code == 200
    vdata = verify_res.json()
    assert vdata["matches"] is False
    assert vdata["expected_hash"] != vdata["calculated_hash"]


# 21. Missing contract returns 404
def test_missing_contract_404():
    random_id = str(uuid.uuid4())
    res = client.post(f"/api/v1/contracts/{random_id}/hash")
    assert res.status_code == 404


# 22. Missing stored hash returns 404 on GET and verify
def test_missing_stored_hash_404():
    fc = create_sample_contract()
    cid = fc.contract_id
    res_get = client.get(f"/api/v1/contracts/{cid}/hash")
    assert res_get.status_code == 404

    res_verify = client.post(f"/api/v1/contracts/{cid}/hash/verify")
    assert res_verify.status_code == 404
