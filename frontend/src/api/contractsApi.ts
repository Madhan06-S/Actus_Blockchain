import { fetchApi } from './client';
import type {
  FinancialContract,
  CandidateTerms,
  RiskStatusResponse,
  ComparisonItem,
  RiskPredictionResponse,
  LiquidityForecastResponse,
  StressTestResponse,
  NegotiationResponse,
  ChatResponse,
} from '../types/contract';
import {
  DEMO_FINANCIAL_CONTRACT,
  DEMO_CANDIDATE_TERMS,
  DEMO_RISK_STATUS,
  DEMO_COMPARISON_ITEMS,
  DEMO_HASH_INFO,
} from '../mock/demoData';

export const contractsApi = {
  // Upload PDF Document (Phase 2 Integration) - Strictly connects to FastAPI endpoint
  async uploadDocument(file: File): Promise<{ document_id: string; filename?: string; extracted_text_snippet?: string }> {
    const formData = new FormData();
    formData.append('file', file);

    let res: Response;
    try {
      res = await fetch('http://localhost:8000/api/v1/documents/upload', {
        method: 'POST',
        body: formData,
      });
    } catch {
      throw new Error("We can't connect to the contract analysis service right now.");
    }

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(errorData.detail || "We couldn't upload this contract. Please try again.");
    }

    return await res.json();
  },

  // Get Extracted Candidate Terms for Document (Phase 2)
  async getExtractedTerms(documentId: string): Promise<CandidateTerms> {
    const res = await fetchApi<{
      document_id: string;
      status: string;
      fields?: Record<string, { value: string | null; confidence: string }>;
      terms?: CandidateTerms;
    }>(`/api/v1/documents/${documentId}/terms`);

    if (res.fields) {
      return {
        principal: res.fields.principal?.value || '100000',
        currency: res.fields.currency?.value || 'INR',
        annual_interest_rate: res.fields.annual_interest_rate?.value || '10.0',
        start_date: res.fields.start_date?.value || '2027-01-01',
        maturity_date: res.fields.maturity_date?.value || '2029-01-01',
        payment_frequency: (res.fields.payment_frequency?.value as any) || 'MONTHLY',
        contract_role: 'RPA',
        confidence: 0.95,
      };
    }
    if (res.terms) {
      return res.terms;
    }
    return DEMO_CANDIDATE_TERMS;
  },

  // Confirm PDF Terms & Create Validated FinancialContract (Phase 2)
  async confirmDocument(documentId: string, terms: CandidateTerms): Promise<{ contract: FinancialContract; terms: CandidateTerms }> {
    const confirmRes = await fetchApi<{
      document_id: string;
      contract_id: string;
      status: string;
      message: string;
    }>(`/api/v1/documents/${documentId}/confirm`, {
      method: 'POST',
      body: JSON.stringify({
        principal: parseFloat(terms.principal) || 100000,
        currency: terms.currency || 'INR',
        annual_interest_rate: parseFloat(terms.annual_interest_rate) || 10.0,
        start_date: terms.start_date || '2027-01-01',
        maturity_date: terms.maturity_date || '2029-01-01',
        payment_frequency: terms.payment_frequency || 'MONTHLY',
        contract_role: terms.contract_role || 'RPA',
        description: `Uploaded contract from document ${documentId.substring(0, 8)}`,
      }),
    });

    const createdContract = await this.getContract(confirmRes.contract_id);
    return { contract: createdContract, terms };
  },

  // Get Financial Contract by ID (Phase 1)
  async getContract(contractId: string): Promise<FinancialContract> {
    try {
      return await fetchApi<FinancialContract>(`/api/v1/contracts/${contractId}`);
    } catch {
      return DEMO_FINANCIAL_CONTRACT;
    }
  },

  // Create Financial Contract (Phase 1)
  async createContract(terms: CandidateTerms): Promise<FinancialContract> {
    try {
      return await fetchApi<FinancialContract>('/api/v1/contracts/', {
        method: 'POST',
        body: JSON.stringify({
          principal: parseFloat(terms.principal) || 100000,
          currency: terms.currency || 'INR',
          annual_interest_rate: parseFloat(terms.annual_interest_rate) || 10.0,
          start_date: terms.start_date || '2027-01-01',
          maturity_date: terms.maturity_date || '2029-01-01',
          payment_frequency: terms.payment_frequency || 'MONTHLY',
          contract_role: terms.contract_role || 'RPA',
          description: 'Directly created ACTUS contract',
        }),
      });
    } catch {
      return DEMO_FINANCIAL_CONTRACT;
    }
  },

  // Get Financial Status & Reconciliation (Phase 8)
  async getStatus(contractId: string): Promise<RiskStatusResponse> {
    try {
      return await fetchApi<RiskStatusResponse>(`/api/v1/contracts/${contractId}/status`);
    } catch {
      return DEMO_RISK_STATUS;
    }
  },

  // Get Payment Comparison Details (Phase 7)
  async getComparison(contractId: string): Promise<{ items: ComparisonItem[] }> {
    try {
      return await fetchApi<{ items: ComparisonItem[] }>(`/api/v1/contracts/${contractId}/blockchain/compare`);
    } catch {
      return { items: DEMO_COMPARISON_ITEMS };
    }
  },

  // Get Hash Integrity Verification (Phase 6 & 7)
  async getHashVerification(contractId: string): Promise<typeof DEMO_HASH_INFO> {
    try {
      return await fetchApi<typeof DEMO_HASH_INFO>(`/api/v1/contracts/${contractId}/blockchain/hash-verification`);
    } catch {
      return DEMO_HASH_INFO;
    }
  },

  // Record Live Payment on MST Blockchain
  async recordPayment(amount: number = 4614.49, contractAddress?: string): Promise<{
    status: string;
    transaction_hash: string;
    block_number: number;
    contract_address: string;
    amount: number;
    explorer_url: string;
  }> {
    return await fetchApi<{
      status: string;
      transaction_hash: string;
      block_number: number;
      contract_address: string;
      amount: number;
      explorer_url: string;
    }>('/api/v1/blockchain/pay', {
      method: 'POST',
      body: JSON.stringify({ amount, contract_address: contractAddress }),
    });
  },

  // --- FINANCIAL INTELLIGENCE ENDPOINTS ---

  // Feature 1: AI Risk Prediction
  async getRiskAnalysis(contractId: string): Promise<RiskPredictionResponse> {
    try {
      return await fetchApi<RiskPredictionResponse>(`/api/v1/contracts/${contractId}/risk`);
    } catch {
      return {
        contract_id: contractId,
        default_probability: 0.18,
        default_probability_percent: 18.0,
        risk_category: 'MEDIUM',
        expected_loss: 18000,
        recommendation: 'APPROVE WITH CONDITIONS',
        model_available: false,
        estimator_type: 'Prototype risk estimator',
        features_used: [
          { name: 'principal', value: 100000, description: 'Loan principal' },
          { name: 'annual_interest_rate', value: 10.0, description: 'Annual interest rate (%)' },
          { name: 'loan_duration_months', value: 24, description: 'Duration in months' },
          { name: 'expected_payment_count', value: 24, description: 'Scheduled payments' },
          { name: 'overdue_payment_count', value: 0, description: 'Overdue count' },
        ],
        message: 'ML risk model is not configured; using prototype risk estimator.',
      };
    }
  },

  // Feature 2: Portfolio Liquidity Engine
  async getLiquidityForecast(payload?: { contract_ids?: string[]; bank_outflows_by_year?: Record<string, number> }): Promise<LiquidityForecastResponse> {
    try {
      return await fetchApi<LiquidityForecastResponse>('/api/v1/liquidity/forecast', {
        method: 'POST',
        body: JSON.stringify(payload || {}),
      });
    } catch {
      return {
        forecast: {
          '2027': { year: '2027', portfolio_inflow: 80000, bank_outflow: 50000, net_liquidity: 30000, status: 'SAFE' },
          '2028': { year: '2028', portfolio_inflow: 75000, bank_outflow: 60000, net_liquidity: 15000, status: 'SAFE' },
          '2029': { year: '2029', portfolio_inflow: 40000, bank_outflow: 70000, net_liquidity: -30000, status: 'DEFICIT_RISK' },
        },
        overall_status: 'DEFICIT_RISK',
        total_inflow: 195000,
        total_outflow: 180000,
        contract_count: 1,
      };
    }
  },

  // Feature 3: Scenario Stress Testing
  async runStressTest(contractId: string, payload: { rate_shock_percent: number; scenario_description?: string }): Promise<StressTestResponse> {
    try {
      return await fetchApi<StressTestResponse>(`/api/v1/contracts/${contractId}/stress-test`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    } catch {
      const shock = payload.rate_shock_percent;
      return {
        contract_id: contractId,
        scenario_description: payload.scenario_description || `Rate shock +${shock}%`,
        base_case: { annual_interest_rate: 10.0, monthly_payment: 4614.49, total_interest: 10747.84, total_repayment: 110747.84, risk_category: 'MEDIUM' },
        stressed_case: { annual_interest_rate: 10.0 + shock, monthly_payment: 4754.20, total_interest: 14100.80, total_repayment: 114100.80, risk_category: 'HIGH' },
        difference: { rate_shock_percent: shock, additional_monthly_payment: 139.71, additional_interest: 3352.96, additional_total_repayment: 3352.96, percentage_increase_in_interest: 31.2 },
        risk_impact: {
          base_risk_category: 'MEDIUM',
          stressed_risk_category: 'HIGH',
          base_default_probability: 0.18,
          stressed_default_probability: 0.27,
          category_shifted: true,
          summary: `Interest rate increase of +${shock}% increases total interest by ₹3,352.96 (31.2% increase).`,
        },
      };
    }
  },

  // Feature 4: Negotiation Agent
  async runNegotiation(contractId: string, payload?: { objective?: string }): Promise<NegotiationResponse> {
    try {
      return await fetchApi<NegotiationResponse>(`/api/v1/contracts/${contractId}/negotiation`, {
        method: 'POST',
        body: JSON.stringify(payload || {}),
      });
    } catch {
      return {
        contract_id: contractId,
        available: false,
        optimized_terms: [
          { parameter: 'annual_interest_rate', current_value: '10.0%', proposed_value: '11.5%', reason: 'Increase margin by +1.5% for credit risk.' },
          { parameter: 'additional_collateral', current_value: 'None', proposed_value: '15% Security Deposit', reason: 'Require partial collateral reserve.' },
        ],
        negotiation_summary: 'Rule-based prototype proposal: Recommended +1.5% rate adjustment and 15% collateral reserve.',
        revised_actus_json: { contractID: `PROPOSED-${contractId}`, status: 'PROPOSED_FOR_HUMAN_REVIEW', nominalInterestRate: 0.115 },
        requires_human_approval: true,
      };
    }
  },

  // Feature 5: AI Chatbot / Financial Assistant
  async sendChatMessage(contractId: string, message: string): Promise<ChatResponse> {
    try {
      return await fetchApi<ChatResponse>(`/api/v1/contracts/${contractId}/chat`, {
        method: 'POST',
        body: JSON.stringify({ message }),
      });
    } catch {
      return {
        contract_id: contractId,
        answer: `AI assistant is not configured; showing data-based answer.\n\nContract ${contractId} is currently showing status DEVIATION_DETECTED because 22 expected scheduled payments remain unpaid.`,
        sources: ['reconciliation', 'actus_schedule'],
        available: false,
      };
    }
  },
};
