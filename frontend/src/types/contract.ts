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

export interface FeatureImportanceItem {
  name: string;
  value: unknown;
  description: string;
}

export interface RiskPredictionResponse {
  contract_id: string;
  default_probability: number | null;
  default_probability_percent: number | null;
  risk_category: 'LOW' | 'MEDIUM' | 'HIGH' | 'NOT_AVAILABLE';
  expected_loss: number | null;
  recommendation: string;
  model_available: boolean;
  estimator_type: string;
  features_used: FeatureImportanceItem[];
  message?: string;
}

export interface YearlyLiquidityItem {
  year: string;
  portfolio_inflow: number;
  bank_outflow: number;
  net_liquidity: number;
  status: 'SAFE' | 'DEFICIT_RISK';
}

export interface LiquidityForecastResponse {
  forecast: Record<string, YearlyLiquidityItem>;
  overall_status: 'SAFE' | 'DEFICIT_RISK';
  total_inflow: number;
  total_outflow: number;
  contract_count: number;
}

export interface StressCaseDetails {
  annual_interest_rate: number;
  monthly_payment: number;
  total_interest: number;
  total_repayment: number;
  default_probability?: number | null;
  risk_category: string;
}

export interface StressDifferenceDetails {
  rate_shock_percent: number;
  additional_monthly_payment: number;
  additional_interest: number;
  additional_total_repayment: number;
  percentage_increase_in_interest: number;
}

export interface StressTestResponse {
  contract_id: string;
  scenario_description: string;
  base_case: StressCaseDetails;
  stressed_case: StressCaseDetails;
  difference: StressDifferenceDetails;
  risk_impact: {
    base_risk_category: string;
    stressed_risk_category: string;
    base_default_probability: number | null;
    stressed_default_probability: number | null;
    category_shifted: boolean;
    summary: string;
  };
}

export interface ProposedTerm {
  parameter: string;
  current_value: string;
  proposed_value: string;
  reason: string;
}

export interface NegotiationResponse {
  contract_id: string;
  available: boolean;
  optimized_terms: ProposedTerm[];
  negotiation_summary: string;
  revised_actus_json: Record<string, unknown>;
  requires_human_approval: boolean;
  message?: string;
}

export interface ChatResponse {
  contract_id: string;
  answer: string;
  sources: string[];
  available: boolean;
  message?: string;
}
