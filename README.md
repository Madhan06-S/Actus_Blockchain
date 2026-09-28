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

## Phase 1 — Financial Contract Input and Validation

### Overview
Phase 1 enables the backend to receive, validate, normalize, and store financial contracts.

Supported Financial Product:
- **FIXED-RATE AMORTIZING LOAN WITH FIXED PERIODIC PAYMENTS**
- Intended future ACTUS contract mapping: **ANN (Annuity)**

### Key Features Implemented in Phase 1
1. **Contract Ingestion & Schema Validation**: Pydantic schema validation for contract creation.
2. **Business Rules Validation**:
   - `principal > 0` (strictly positive monetary amounts)
   - `annual_interest_rate >= 0` (non-negative percentage)
   - `start_date < maturity_date` (strict date order)
   - `currency` non-empty string
   - Supported `payment_frequency` (`MONTHLY`) and `contract_role` (`RPA`, `RPL`)
3. **Monetary Precision**: Uses Python's `Decimal` type to avoid binary floating-point representation issues.
4. **Unique Identification & Timestamps**: Assigns UUID v4 `contract_id` and UTC `created_at` timestamp.
5. **In-Memory Storage**: Repository pattern decoupling API logic from persistence (`ContractRepository`).

### Example Valid Request (`POST /api/v1/contracts`)

```json
{
    "principal": 100000,
    "currency": "INR",
    "annual_interest_rate": 10.0,
    "start_date": "2027-01-01",
    "maturity_date": "2029-01-01",
    "payment_frequency": "MONTHLY",
    "contract_role": "RPA",
    "description": "Example fixed-rate amortizing loan"
}
```

### Example Response (HTTP 201 Created)

```json
{
    "contract_id": "02058345-4328-4cb9-8fe1-17930f416efd",
    "principal": "100000",
    "currency": "INR",
    "annual_interest_rate": "10.0",
    "start_date": "2027-01-01",
    "maturity_date": "2029-01-01",
    "payment_frequency": "MONTHLY",
    "contract_role": "RPA",
    "description": "Example fixed-rate amortizing loan",
    "status": "VALIDATED",
    "created_at": "2026-09-28T16:36:59.924436Z"
}
```

---

## Phase 1 Limitations

> [!IMPORTANT]
> **Phase 1 Notice**: Monthly installment calculation, interest accrual calculations, ACTUS event generation, cash-flow schedules, blockchain integration, smart contracts, and risk logic are intentionally NOT implemented in Phase 1.

---

## Available API Endpoints

- `GET /`: Returns basic system running status.
- `GET /health`: Returns system health check status.
- `POST /api/v1/contracts`: Validates, normalizes, and stores a financial contract (returns 201 Created).
- `GET /api/v1/contracts/{contract_id}`: Retrieves stored contract by ID (returns 404 if missing).
- `GET /api/v1/contracts`: Lists all stored contracts in memory.

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

To start the FastAPI server with hot-reload enabled:

```bash
uvicorn app.main:app --reload --port 8000
```

Once running, access the interactive API docs at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 5. Run Automated Tests

Execute `pytest` to run all unit and API tests:

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
│   │   │       ├── contracts.py
│   │   │       └── health.py
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── common.py
│   │   │   └── contract.py
│   │   │
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── contract_repository.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── common.py
│   │   │   └── contract.py
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── contract_service.py
│   │       └── health_service.py
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_contracts.py
│       └── test_health.py
│
├── docs/
│   └── architecture.md
│
├── .env
├── .env.example
├── .gitignore
├── pytest.ini
├── README.md
└── requirements.txt
```
