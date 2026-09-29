export type ContractRole = 'RPA' | 'RPL';
export type PaymentFrequency = 'MONTHLY' | 'QUARTERLY' | 'ANNUALLY';
export type FinancialStatus = 'ON_TRACK' | 'DEVIATION_DETECTED' | 'OVERDUE' | 'COMPLETED';
export type BlockchainStatus = 'ACTIVE' | 'COMPLETED' | 'DEFAULTED' | 'TERMINATED';
export type ReconciliationStatus = 'MATCHED' | 'AMOUNT_VARIANCE' | 'DATE_VARIANCE' | 'UNPAID' | 'UNEXPECTED';

export interface FinancialContract {
  contract_id: string;
  principal: string;
  currency: string;
  annual_interest_rate: string;
  start_date: string;
  maturity_date: string;
  payment_frequency: PaymentFrequency;
  contract_role: ContractRole;
  description?: string;
  status: string;
  created_at: string;
}

export interface CandidateTerms {
  principal: string;
  currency: string;
  annual_interest_rate: string;
  payment_frequency: PaymentFrequency;
  start_date: string;
  maturity_date: string;
  contract_role: ContractRole;
  confidence: number;
}

export interface ActusContract {
  contract_id: string;
  actus_contract_type: 'ANN' | 'PAM' | 'LAM';
  mapping_status: string;
  terms: Record<string, unknown>;
}

export interface ActusEvent {
  event_id: string;
  contract_id: string;
  event_type: 'IED' | 'IP' | 'PR' | 'PP' | 'MD';
  event_time: string;
  sequence: number;
  event_status: string;
  event_reference?: string;
}

export interface CashFlow {
  cash_flow_id: string;
  contract_id: string;
  event_id: string;
  event_type: string;
  event_time: string;
  currency: string;
  opening_principal: string;
  interest_amount: string;
  principal_amount: string;
  total_amount: string;
  closing_principal: string;
  cash_flow_direction: string;
  net_cash_flow: string;
}

export interface CashFlowResult {
  contract_id: string;
  actus_contract_type: string;
  currency: string;
  initial_principal: string;
  total_interest: string;
  total_principal: string;
  total_cash_flow: string;
  final_outstanding_principal: string;
  cash_flows: CashFlow[];
}

export interface ActualPayment {
  payment_id: string;
  transaction_hash: string;
  block_number: number;
  timestamp: string;
  payer: string;
  payee: string;
  amount: string;
  payment_index: number;
}

export interface ComparisonItem {
  item_id: string;
  expected_event_type: string;
  expected_date: string;
  expected_amount: string;
  actual_payment: ActualPayment | null;
  status: ReconciliationStatus;
  amount_variance: string;
  date_variance_days: number;
  notes: string;
}

export interface RiskStatusResponse {
  contract_id: string;
  blockchain_contract_address: string | null;
  overall_status: FinancialStatus;
  blockchain_status: BlockchainStatus | null;
  hash_integrity_matched: boolean;
  total_expected_amount: string;
  total_actual_paid: string;
  net_amount_variance: string;
  total_expected_payments: number;
  matched_payment_count: number;
  unpaid_payment_count: number;
  overdue_payment_count: number;
  unexpected_payment_count: number;
  evaluation_date: string;
  status_reasons: string[];
}
