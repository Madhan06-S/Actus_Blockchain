# ACTUS-Powered Programmable Financial Contracts on MST Blockchain

## Project Overview

This project builds a backend system for **ACTUS-Powered Programmable Financial Contracts on MST Blockchain**. The platform standardizes complex financial contracts (such as loans, bonds, and derivatives) using the **ACTUS (Algorithmic Contract Types Unified Standard)** framework and connects them with smart contracts on the **MST Blockchain** for automated execution, settlement, and risk monitoring.

---

## Team Responsibilities

### Person 1 (Backend & Financial Logic Lead - My Responsibility)
- Financial contract input & schema validation
- ACTUS standard integration & mapping
- ACTUS event generation (principal payments, interest payments, etc.)
- Cash-flow simulation engine
- Cryptographic contract hashing
- Expected-vs-actual payment comparison engine
- Risk status evaluation logic
- RESTful API design & backend integration endpoints

### Person 2 (Blockchain & Smart Contract Lead)
- Solidity smart contract development
- MST Blockchain deployment & network management
- Wallet integrations & signing
- On-chain token/cash movement transactions
- Blockchain event generation & listening
- Smart contract state management

---

## Eventual System Architecture

```
Financial Contract
        ↓
Contract Validation
        ↓
ACTUS Representation
        ↓
Expected Contractual Events
        ↓
Expected Cash Flows
        ↓
Contract Hash
        ↓
MST Blockchain Smart Contract
        ↓
Actual Blockchain Events
        ↓
Expected vs Actual Comparison
        ↓
Risk / Contract Status
        ↓
Dashboard
```

---

## Phase 4 — ACTUS Event Generation

### Overview
Phase 4 translates validated `ActusContract` models into an ordered, deterministic timeline of **Expected Contractual Events** (`ActusEvent`).

### Key Features & Design Rules
1. **Official ACTUS Event Types**:
   - `IED`: Initial Exchange Date (Initial principal disbursement/exchange).
   - `IP`: Interest Payment (Periodic scheduled interest payment).
   - `PR`: Principal Redemption (Periodic scheduled principal repayment for `ANN`/`LAM`).
   - `PP`: Principal Prepayment (Generated only when explicit prepayment terms exist).
   - `MD`: Maturity Date (Contract maturity event).
2. **Contract Type Event Logic**:
   - **ANN (Annuity)**: Generates `IED`, periodic `IP` events, periodic `PR` events, and `MD`.
   - **PAM (Principal at Maturity)**: Generates `IED`, periodic `IP` events, and `MD`. Periodic `PR` events are **NOT** generated.
   - **LAM (Linear Amortizing)**: Generates `IED`, periodic `IP` events, periodic `PR` events, and `MD`.
3. **Calendar Month Arithmetic**: `P1M` cycle dates use exact calendar month arithmetic (`Jan 31` → `Feb 28/29` → `Mar 31`), avoiding 30-day approximations.
4. **Deterministic Event Sorting**: Events are ordered by `event_time`, then by ACTUS priority (`IED` → `PR` → `IP` → `PP` → `MD`).
5. **No Cash-Flow Simulation**: Monetary cash-flow amounts and amortization engines are intentionally deferred to Phase 5.

### Example Event Generation Response (`POST /api/v1/contracts/{contract_id}/actus/events`)

```json
{
  "contract_id": "02058345-4328-4cb9-8fe1-17930f416efd",
  "actus_contract_type": "ANN",
  "generation_status": "GENERATED",
  "total_events": 50,
  "events": [
    {
      "event_id": "e1a2b3c4-0000-0000-0000-000000000001",
      "contract_id": "02058345-4328-4cb9-8fe1-17930f416efd",
      "event_type": "IED",
      "event_time": "2027-01-01T00:00:00Z",
      "sequence": 1,
      "event_status": "EXPECTED",
      "source_actus_contract_id": "02058345-4328-4cb9-8fe1-17930f416efd",
      "event_reference": "Initial Principal Exchange"
    },
    {
      "event_id": "e1a2b3c4-0000-0000-0000-000000000002",
      "contract_id": "02058345-4328-4cb9-8fe1-17930f416efd",
      "event_type": "PR",
      "event_time": "2027-02-01T00:00:00Z",
      "sequence": 2,
      "event_status": "EXPECTED",
      "source_actus_contract_id": "02058345-4328-4cb9-8fe1-17930f416efd",
      "event_reference": "Scheduled Principal Redemption"
    },
    {
      "event_id": "e1a2b3c4-0000-0000-0000-000000000003",
      "contract_id": "02058345-4328-4cb9-8fe1-17930f416efd",
      "event_type": "IP",
      "event_time": "2027-02-01T00:00:00Z",
      "sequence": 3,
      "event_status": "EXPECTED",
      "source_actus_contract_id": "02058345-4328-4cb9-8fe1-17930f416efd",
      "event_reference": "Scheduled Interest Payment"
    }
  ],
  "warnings": [],
  "missing_attributes": []
}
```

---

## Available API Endpoints

- `GET /`: Basic system running status.
- `GET /health`: Health check indicator.
- `POST /api/v1/contracts`: Creates and validates a financial contract.
- `GET /api/v1/contracts/{contract_id}`: Retrieves stored financial contract by ID.
- `GET /api/v1/contracts`: Lists all stored financial contracts.
- `POST /api/v1/documents/upload`: Uploads PDF document (max 10 MB).
- `GET /api/v1/documents/{id}/terms`: Retrieves extracted candidate financial terms.
- `POST /api/v1/documents/{id}/confirm`: Confirms terms and creates a validated `FinancialContract`.
- `POST /api/v1/contracts/{contract_id}/actus`: Generates and stores ACTUS contract mapping.
- `GET /api/v1/contracts/{contract_id}/actus`: Retrieves stored ACTUS contract mapping.
- `POST /api/v1/contracts/{contract_id}/actus/events`: Generates and stores expected ACTUS contractual event schedule.
- `GET /api/v1/contracts/{contract_id}/actus/events`: Retrieves expected ACTUS contractual event schedule.
- `POST /api/v1/contracts/{contract_id}/actus/cash-flows`: Generates and stores expected monetary cash flows and amortization schedule.
- `GET /api/v1/contracts/{contract_id}/actus/cash-flows`: Retrieves expected monetary cash flows and amortization schedule.
- `POST /api/v1/contracts/{contract_id}/hash`: Generates canonical payload and SHA-256 integrity hash.
- `GET /api/v1/contracts/{contract_id}/hash`: Retrieves stored SHA-256 integrity hash and canonical payload.
- `POST /api/v1/contracts/{contract_id}/hash/verify`: Recalculates SHA-256 hash and verifies integrity against stored hash.

---

## Phase 5 — Cash-Flow Simulation for ACTUS Expected Events

### Overview
Phase 5 converts expected ACTUS contractual events (`ActusEvent`) into expected monetary cash flows (`CashFlow` & `CashFlowSimulationResult`).

### Key Features & Design Rules
1. **ANN (Annuity) Support**: Calculates stateful amortization for fixed-rate amortizing loans.
2. **PMT Periodic Payment Calculation**: Uses exact Decimal financial arithmetic for monthly payments:
   $$PMT = P \times \frac{r(1+r)^n}{(1+r)^n - 1}$$
3. **Stateful Amortization Schedule**:
   - Maintains opening principal, monthly interest portion ($I_t = P_{t-1} \times r$), principal repayment portion ($PR_t = PMT - I_t$), and closing principal balance ($P_t = P_{t-1} - PR_t$).
   - Reconciles final maturity repayment so `final_outstanding_principal == 0.00`.
4. **Event Aggregation**: Combines co-occurring `PR` and `IP` events into a single economic payment record (`PR_IP`) while retaining reference event IDs.
5. **Sign & Direction Semantics**:
   - **RPA** (Lender): Initial disbursement `IED` is `OUTFLOW` ($-P$), repayments are `INFLOW` ($+PMT$).
   - **RPL** (Borrower): Initial disbursement `IED` is `INFLOW` ($+P$), repayments are `OUTFLOW` ($-PMT$).
6. **Decimal Currency Quantization**: Standardized monetary rounding to 2 decimal places (`ROUND_HALF_UP`) for display and `0.01` tolerance for residual balance reconciliation.

---

## Phase 6 — Contract Hashing and Integrity Verification

### Overview
Phase 6 creates a deterministic SHA-256 cryptographic fingerprint (`ContractHash`) over off-chain financial contract terms and ACTUS mapping data. This hash anchors contract identity for future on-chain verification on the MST Blockchain.

### Key Features & Design Rules
1. **Canonicalization (`v1`)**: Normalizes Decimal values (`100000.0` -> `"100000.00"`), ISO dates (`YYYY-MM-DD`), and string formats.
2. **Explicit Allow-List**: Includes core economic terms (`principal`, `currency`, `annual_interest_rate`, `start_date`, `maturity_date`, `payment_frequency`, `contract_role`, ACTUS terms) and excludes non-contractual runtime state (`created_at`, database IDs, UUIDs).
3. **Deterministic Serialization**: Enforces lexicographical key sorting (`sort_keys=True`), compact JSON separators (`,`, `:`), and UTF-8 encoding.
4. **SHA-256 Hash Digest**: Uses Python standard library `hashlib.sha256` to output a 64-character lowercase hexadecimal string.
5. **Integrity Verification**: Endpoint `/hash/verify` recalculates the SHA-256 digest from live contract data and detects any unauthorized modifications.

---

## Setup & Running Instructions

### Prerequisites
- **Python 3.11+** installed on your system.

### 1. Create a Virtual Environment

On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 4. Run the Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

Access interactive API docs at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 5. Run Automated Tests

Execute `pytest` to run all test suites (120 total tests):

```bash
pytest
```

---

## Project Structure

```
Actus_blockchain/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── actus.py
│   │   │       ├── actus_events.py
│   │   │       ├── cash_flows.py
│   │   │       ├── contract_hash.py
│   │   │       ├── contracts.py
│   │   │       ├── documents.py
│   │   │       └── health.py
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── actus.py
│   │   │   ├── actus_event.py
│   │   │   ├── cash_flow.py
│   │   │   ├── common.py
│   │   │   ├── contract.py
│   │   │   ├── contract_hash.py
│   │   │   └── document.py
│   │   │
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── actus_event_repository.py
│   │   │   ├── actus_repository.py
│   │   │   ├── cash_flow_repository.py
│   │   │   ├── contract_hash_repository.py
│   │   │   ├── contract_repository.py
│   │   │   └── document_repository.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── actus.py
│   │   │   ├── actus_event.py
│   │   │   ├── cash_flow.py
│   │   │   ├── common.py
│   │   │   ├── contract.py
│   │   │   ├── contract_hash.py
│   │   │   └── document.py
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── actus_cycle.py
│   │       ├── actus_event_generator.py
│   │       ├── actus_event_service.py
│   │       ├── actus_mapper.py
│   │       ├── actus_service.py
│   │       ├── cash_flow_calculator.py
│   │       ├── cash_flow_service.py
│   │       ├── contract_canonicalizer.py
│   │       ├── contract_hash_service.py
│   │       ├── contract_hasher.py
│   │       ├── contract_service.py
│   │       ├── contract_term_extractor.py
│   │       ├── document_service.py
│   │       ├── document_text_extractor.py
│   │       └── health_service.py
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_actus.py
│       ├── test_actus_events.py
│       ├── test_cash_flows.py
│       ├── test_contract_hash.py
│       ├── test_contracts.py
│       ├── test_documents.py
│       └── test_health.py
│
├── docs/
│   └── architecture.md
│
├── storage/
│   └── documents/        (Ignored in .gitignore)
│
├── .env
├── .env.example
├── .gitignore
├── pytest.ini
├── README.md
└── requirements.txt
```
