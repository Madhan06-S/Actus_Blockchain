import type { CandidateTerms, FinancialContract, RiskStatusResponse, ComparisonItem } from '../types/contract';

export const DEMO_CONTRACT_ID = "847f744d-3a10-41ea-8f63-0c450a60410a";
export const DEMO_BLOCKCHAIN_ADDRESS = "0x8f3b2a91c4d7e65f012b34567890abcdef123456";

export const DEMO_CANDIDATE_TERMS: CandidateTerms = {
  principal: "100000.00",
  currency: "INR",
  annual_interest_rate: "10.00",
  payment_frequency: "MONTHLY",
  start_date: "2027-01-01",
  maturity_date: "2029-01-01",
  contract_role: "RPA",
  confidence: 0.98,
};

export const DEMO_FINANCIAL_CONTRACT: FinancialContract = {
  contract_id: DEMO_CONTRACT_ID,
  principal: "100000.00",
  currency: "INR",
  annual_interest_rate: "10.00",
  start_date: "2027-01-01",
  maturity_date: "2029-01-01",
  payment_frequency: "MONTHLY",
  contract_role: "RPA",
  description: "Fixed-Rate Annuity Financial Contract",
  status: "VALIDATED",
  created_at: new Date().toISOString(),
};

export const DEMO_RISK_STATUS: RiskStatusResponse = {
  contract_id: DEMO_CONTRACT_ID,
  blockchain_contract_address: DEMO_BLOCKCHAIN_ADDRESS,
  overall_status: "DEVIATION_DETECTED",
  blockchain_status: "COMPLETED",
  hash_integrity_matched: true,
  total_expected_amount: "110747.84",
  total_actual_paid: "100000.00",
  net_amount_variance: "-10747.84",
  total_expected_payments: 24,
  matched_payment_count: 2,
  unpaid_payment_count: 22,
  overdue_payment_count: 0,
  unexpected_payment_count: 0,
  evaluation_date: new Date().toISOString(),
  status_reasons: [
    "The contract schedule expects 24 monthly payments totaling ₹1,10,747.84.",
    "The recorded activity on blockchain contains 2 payments totaling ₹1,00,000.00.",
    "22 expected scheduled payments have not yet been recorded.",
    "On-chain Solidity contract status has reached COMPLETED (principal settled).",
    "Off-chain ACTUS financial schedule is not fully satisfied due to outstanding interest schedule.",
    "Off-chain SHA-256 hash matches on-chain actusHash."
  ],
};

export const DEMO_COMPARISON_ITEMS: ComparisonItem[] = [
  {
    item_id: "comp-1",
    expected_event_type: "PR_IP",
    expected_date: "2027-02-01",
    expected_amount: "4614.49",
    actual_payment: {
      payment_id: "pay-1",
      transaction_hash: "0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b",
      block_number: 14892301,
      timestamp: "2026-09-28T14:30:00Z",
      payer: "0x1111111111111111111111111111111111111111",
      payee: "0x2222222222222222222222222222222222222222",
      amount: "25000.00",
      payment_index: 1,
    },
    status: "AMOUNT_VARIANCE",
    amount_variance: "20385.51",
    date_variance_days: -126,
    notes: "Recorded earlier on blockchain with higher initial payment"
  },
  {
    item_id: "comp-2",
    expected_event_type: "PR_IP",
    expected_date: "2027-03-01",
    expected_amount: "4614.49",
    actual_payment: {
      payment_id: "pay-2",
      transaction_hash: "0x1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0e1d2c3b4a5f6e7d8c9b0a1f2e",
      block_number: 14892345,
      timestamp: "2026-09-28T15:10:00Z",
      payer: "0x1111111111111111111111111111111111111111",
      payee: "0x2222222222222222222222222222222222222222",
      amount: "75000.00",
      payment_index: 2,
    },
    status: "AMOUNT_VARIANCE",
    amount_variance: "70385.51",
    date_variance_days: -154,
    notes: "Recorded bulk payment settling principal on-chain"
  },
  ...Array.from({ length: 22 }, (_, idx) => {
    const month = idx + 3;
    const year = 2027 + Math.floor((month - 1) / 12);
    const mNum = ((month - 1) % 12) + 1;
    const dateStr = `${year}-${mNum < 10 ? '0' + mNum : mNum}-01`;
    return {
      item_id: `comp-${idx + 3}`,
      expected_event_type: "PR_IP",
      expected_date: dateStr,
      expected_amount: idx === 21 ? "4614.57" : "4614.49",
      actual_payment: null,
      status: "UNPAID" as const,
      amount_variance: "-4614.49",
      date_variance_days: 0,
      notes: "Future expected scheduled payment"
    };
  })
];

export const DEMO_HASH_INFO = {
  contract_id: DEMO_CONTRACT_ID,
  backend_sha256_hash: "3a183e4452a503887a70831bab73c4866c78b5533a12b4c5d6e7f8a9b0c1d2e3",
  blockchain_actus_hash: "3a183e4452a503887a70831bab73c4866c78b5533a12b4c5d6e7f8a9b0c1d2e3",
  is_match: true,
  algorithm: "SHA-256",
};

/** Returns the currency symbol for a given ISO 4217 code. */
export function getCurrencySymbol(currency: string): string {
  const map: Record<string, string> = {
    INR: '₹',
    USD: '$',
    EUR: '€',
    GBP: '£',
  };
  return map[currency?.toUpperCase()] ?? currency ?? '₹';
}

/** Returns a locale-formatted currency string, using Indian grouping for INR. */
export function formatAmount(amount: number, currency: string): string {
  const curr = currency?.toUpperCase() || 'INR';
  const locale = curr === 'INR' ? 'en-IN' : 'en-US';
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: curr,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function generateDynamicContractData(terms: CandidateTerms, contractId: string = "fc-" + Date.now()): {
  contract: FinancialContract;
  statusData: RiskStatusResponse;
  comparisonItems: ComparisonItem[];
} {
  const principalNum = parseFloat(terms.principal) || 100000;
  const rateNum = parseFloat(terms.annual_interest_rate) || 10.0;
  const startDate = terms.start_date || "2027-01-01";
  const maturityDate = terms.maturity_date || "2029-01-01";

  const sDate = new Date(startDate);
  const mDate = new Date(maturityDate);
  const totalMonths = Math.max(1, (mDate.getFullYear() - sDate.getFullYear()) * 12 + (mDate.getMonth() - sDate.getMonth()));
  const totalYears = totalMonths / 12;

  const totalInterest = (principalNum * (rateNum / 100)) * totalYears;
  const totalExpected = principalNum + totalInterest;
  const monthlyEmi = totalExpected / totalMonths;

  const contract: FinancialContract = {
    contract_id: contractId,
    principal: principalNum.toFixed(2),
    currency: terms.currency || "INR",
    annual_interest_rate: rateNum.toFixed(2),
    start_date: startDate,
    maturity_date: maturityDate,
    payment_frequency: terms.payment_frequency || "MONTHLY",
    contract_role: terms.contract_role || "RPA",
    description: `ACTUS Financial Contract (Principal: ${terms.currency || "INR"} ${principalNum.toLocaleString()})`,
    status: "VALIDATED",
    created_at: new Date().toISOString(),
  };

  const comparisonItems: ComparisonItem[] = Array.from({ length: totalMonths }, (_, idx) => {
    const curDate = new Date(sDate);
    curDate.setMonth(curDate.getMonth() + idx + 1);
    const dateStr = curDate.toISOString().split("T")[0];

    return {
      item_id: `item-${idx + 1}`,
      expected_event_type: "PR_IP",
      expected_date: dateStr,
      expected_amount: monthlyEmi.toFixed(2),
      actual_payment: null,
      status: "UNPAID" as const,
      amount_variance: `-${monthlyEmi.toFixed(2)}`,
      date_variance_days: 0,
      notes: `Scheduled monthly installment ${idx + 1}/${totalMonths}`,
    };
  });

  const currency = terms.currency?.toUpperCase() || 'INR';

  const statusData: RiskStatusResponse = {
    contract_id: contractId,
    blockchain_contract_address: "0xf99F2d28720AC7019F6b2fb9837a86f3b4901FBE",
    overall_status: "DEVIATION_DETECTED",
    blockchain_status: "ACTIVE",
    hash_integrity_matched: true,
    total_expected_amount: totalExpected.toFixed(2),
    total_actual_paid: "0.00",
    net_amount_variance: `-${totalExpected.toFixed(2)}`,
    total_expected_payments: totalMonths,
    matched_payment_count: 0,
    unpaid_payment_count: totalMonths,
    overdue_payment_count: 0,
    unexpected_payment_count: 0,
    evaluation_date: new Date().toISOString(),
    status_reasons: [
      `The contract schedule expects ${totalMonths} monthly payments totaling ${formatAmount(totalExpected, currency)}.`,
      `${totalMonths} scheduled payments pending on MST Blockchain.`,
      `ACTUS financial schedule initialized successfully.`
    ],
  };

  return { contract, statusData, comparisonItems };
}

