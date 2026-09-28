# System Architecture Specification

## Overview

The **ACTUS-Powered Programmable Financial Contracts on MST Blockchain** system links off-chain standardized financial contract logic (ACTUS standard) with on-chain programmable execution on the **MST Blockchain**.

---

## High-Level Architecture Flow

```mermaid
flowchart TD
    A[Frontend UI / Dashboard] --> B[FastAPI Backend]
    B --> C[Financial Contract Service]
    C --> D[ACTUS Service & Mapper]
    D --> E[ACTUS Event Generator]
    E --> F[Cash Flow Service]
    F --> G[Comparison & Risk Service]
    G --> H[Blockchain Integration Layer]
    H --> I[MST Blockchain Smart Contracts]
```

---

## End-to-End System Pipeline (Phase 0 – Phase 6)

```mermaid
flowchart TD
    A[PDF Document Upload] -->|POST /api/v1/documents/upload| B[Document Service]
    B -->|pypdf Text Extraction| C[Contract Term Extractor]
    C -->|Candidate Terms| D[Human Confirmation]
    D -->|POST /api/v1/documents/id/confirm| E[Contract Service]
    E -->|Phase 1 Validation| F[Validated FinancialContract]
    F -->|POST /api/v1/contracts/id/actus| G[ACTUS Mapper & Service]
    G -->|Phase 3 ActusContract| H[ActusContract Representation]
    H -->|POST /api/v1/contracts/id/actus/events| I[ACTUS Event Generator]
    I -->|Phase 4 Events Timeline| J[Expected Contractual Events]
    J -->|POST /api/v1/contracts/id/actus/cash-flows| K[Cash Flow Calculator]
    K -->|Phase 5 Amortization| L[Cash Flow Simulation Result]
    F & H -->|POST /api/v1/contracts/id/hash| M[Contract Canonicalizer & Hasher]
    M -->|Phase 6 Canonical Payload v1| N[SHA-256 Digest 64-hex]
```

---

## Phase 6 Contract Hashing & Integrity Verification Specification

Phase 6 creates a deterministic 64-character lowercase hexadecimal **SHA-256 integrity fingerprint** for off-chain contracts to enable future smart contract state anchoring on the MST Blockchain.

### Key Principles & Features:
1. **Canonical Payload Version `v1`**:
   - Explicit allow-list of contractual terms from `FinancialContract` and `ActusContract`.
   - Excludes non-contractual runtime fields (`created_at`, `updated_at`, `cash_flow_id`, `event_id`, database UUIDs).
2. **Deterministic Serialization**:
   - Normalizes Decimal fields (`100000.0` -> `"100000.00"`), dates (`YYYY-MM-DD`), and string casing.
   - Enforces key sorting (`sort_keys=True`), compact separators (`,`, `:`), and UTF-8 byte encoding.
3. **Cryptographic Algorithm**: Standard `hashlib.sha256` produces a 64-character hex digest.
4. **Integrity Verification**: `POST /hash/verify` recalculates the canonical SHA-256 hash from live state and checks for tampering against the stored hash.

---

## Phase 5 Cash-Flow Simulation Specification

Phase 5 converts expected contractual events (`ActusEvent`) into expected monetary cash flows (`CashFlow` & `CashFlowSimulationResult`).

### Key Principles & Features:
1. **Product Support**: Initially supports **ANN** (Annuity) contracts. Unsupported types return `CALCULATION_UNSUPPORTED`.
2. **Stateful Amortization**:
   - Calculates periodic annuity payment (PMT) using exact formulas:
     $$PMT = P \times \frac{r(1+r)^n}{(1+r)^n - 1}$$
   - Tracks opening principal, interest portion ($I_t = P_{t-1} \times r$), principal portion ($PR_t = PMT - I_t$), and closing principal ($P_t = P_{t-1} - PR_t$).
   - Reconciles final maturity payment so `final_outstanding_principal == 0.00`.
3. **Event Combination**: Combines co-occurring `PR` and `IP` events into a single economic payment (`PR_IP`) while maintaining event references.
4. **Sign & Role Conventions**:
   - **RPA** (Lender/Investor): Initial exchange `IED` is an `OUTFLOW` ($-P$), periodic payments are `INFLOW` ($+PMT$).
   - **RPL** (Borrower): Initial exchange `IED` is an `INFLOW` ($+P$), periodic payments are `OUTFLOW` ($-PMT$).
5. **Decimal Precision**: Uses `Decimal` arithmetic with 2-decimal place quantization (`ROUND_HALF_UP`) for display and 0.01 tolerance for zero reconciliation.

---

## Phase 4 ACTUS Event Generation Specification

Phase 4 converts a validated `ActusContract` model into an ordered timeline of **Expected Contractual Events** (`ActusEvent`).

> [!IMPORTANT]
> **Expected Events vs. Actual Payments**: Generated ACTUS events represent expected contractual schedule points (e.g., when interest payments or principal redemptions are contractually due). They are **NOT** actual payment settlements, monetary cash-flow calculations, or blockchain transactions. Monetary cash-flow amounts and amortization engines belong to Phase 5.

### 1. ACTUS Event Types & Semantics

| Event Type | Full Name | Semantic Description | Contract Types Applied |
| :--- | :--- | :--- | :--- |
| **IED** | Initial Exchange Date | Initial principal disbursement/exchange date | `ANN`, `PAM`, `LAM` |
| **IP** | Interest Payment | Periodic scheduled interest payment date | `ANN`, `PAM`, `LAM` |
| **PR** | Principal Redemption | Periodic scheduled principal repayment date | `ANN`, `LAM` |
| **PP** | Principal Prepayment | Unscheduled prepayment event | Generated ONLY if explicit prepayment terms exist |
| **MD** | Maturity Date | Final contract maturity date | `ANN`, `PAM`, `LAM` |

---

### 2. Cycle Date Generation & Calendar Arithmetic

Cycle dates (e.g. `P1M` for monthly cycles) are generated deterministically using calendar month arithmetic (`add_calendar_months`).
- **Calendar Month Rules**: The generator does **NOT** approximate calendar months with 30-day increments.
  - *Example*: A monthly cycle starting on `Jan 31` generates `Feb 28` (or `Feb 29` leap year), `Mar 31`, `Apr 30`, `May 31`.
- **Date Boundaries**: No events are generated past `maturityDate`.

---

### 3. Deterministic Event Ordering Rules

When multiple events occur at the exact same timestamp, events are ordered deterministically by ACTUS priority sequence:
1. `IED` (Priority 1)
2. `PR` (Priority 2)
3. `IP` (Priority 3)
4. `PP` (Priority 4)
5. `MD` (Priority 5)

---

## Architectural Responsibility Boundaries

The system is strictly divided into **Off-Chain** processing and **On-Chain** state management & validation.

### 1. OFF-CHAIN Components (Backend Service Boundary - Person 1)
- **Full Contract Ingestion & Parsing**: Raw contract storage and validation.
- **ACTUS Standard Modeling (Phase 3)**: Formal ACTUS Data Dictionary translation (`ActusContract`).
- **ACTUS Event Generation (Phase 4)**: Generating expected contractual event timelines (`IED`, `IP`, `PR`, `MD`).
- **Cash-Flow Simulation (Phase 5)**: Amortization schedule and cash flow monetary amount calculations.
- **Contract Hashing (Phase 6)**: Cryptographic hashing of canonical contract state for on-chain anchoring.
- **Expected vs. Actual Comparison (Phase 7)**: Reconciling on-chain transactions against off-chain schedules.

---

### 2. ON-CHAIN Components (Smart Contract Boundary - Person 2)
- **Contract Metadata & Hash Anchoring**: Storing immutable contract ID and cryptographic state hash.
- **State Machine & Settlement Events**: Managing on-chain execution, tokenized cash movements, and payment events.
