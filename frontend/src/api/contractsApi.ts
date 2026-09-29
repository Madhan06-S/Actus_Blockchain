import { fetchApi } from './client';
import type {
  FinancialContract,
  CandidateTerms,
  RiskStatusResponse,
  ComparisonItem,
} from '../types/contract';
import {
  DEMO_CANDIDATE_TERMS,
  DEMO_FINANCIAL_CONTRACT,
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
        // NOTE: Do not set Content-Type header manually for multipart/form-data.
        // The browser automatically sets boundary headers.
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

  // Confirm PDF Terms & Extract Candidates (Phase 2)
  async confirmDocument(documentId: string): Promise<{ terms: CandidateTerms }> {
    try {
      return await fetchApi<{ terms: CandidateTerms }>(`/api/v1/documents/${documentId}/confirm`, {
        method: 'POST',
      });
    } catch {
      return { terms: DEMO_CANDIDATE_TERMS };
    }
  },

  // Create Financial Contract (Phase 1)
  async createContract(terms: CandidateTerms): Promise<FinancialContract> {
    try {
      return await fetchApi<FinancialContract>('/api/v1/contracts/', {
        method: 'POST',
        body: JSON.stringify(terms),
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
};
