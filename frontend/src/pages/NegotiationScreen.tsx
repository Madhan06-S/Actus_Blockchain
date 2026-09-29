import React, { useState } from 'react';
import { Handshake, FileEdit, CheckCircle2 } from 'lucide-react';
import type { FinancialContract, NegotiationResponse } from '../types/contract';
import { contractsApi } from '../api/contractsApi';

interface NegotiationScreenProps {
  contract: FinancialContract;
}

export const NegotiationScreen: React.FC<NegotiationScreenProps> = ({ contract }) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [negData, setNegData] = useState<NegotiationResponse | null>(null);
  const [showJson, setShowJson] = useState<boolean>(false);

  const handleRunNegotiation = async () => {
    setLoading(true);
    try {
      const res = await contractsApi.runNegotiation(contract.contract_id, {
        objective: 'Reduce lender risk while keeping terms realistic',
      });
      setNegData(res);
    } catch (err) {
      console.warn('Negotiation API fallback:', err);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    handleRunNegotiation();
  }, []);

  return (
    <div style={{ padding: '2rem 2.5rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* HEADER */}
      <div
        style={{
          backgroundColor: '#ffffff',
          padding: '1.5rem 2rem',
          borderRadius: '14px',
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.05)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '0.75rem', borderRadius: '10px', backgroundColor: '#f0f9ff', color: '#0284c7' }}>
            <Handshake size={28} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              AI Negotiation Assistant
            </h2>
            <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.2rem' }}>
              Generate risk-mitigating proposed term adjustments for human review
            </div>
          </div>
        </div>

        <button
          onClick={handleRunNegotiation}
          className="btn-primary"
          disabled={loading}
          style={{ fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <FileEdit size={16} />
          {loading ? 'Analyzing...' : 'Generate New Proposals'}
        </button>
      </div>

      {/* HUMAN APPROVAL NOTICE */}
      <div
        style={{
          backgroundColor: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '12px',
          padding: '1.25rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
        }}
      >
        <CheckCircle2 size={24} color="#1d4ed8" />
        <div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#1e3a8a' }}>
            Requires Human Approval
          </div>
          <div style={{ fontSize: '0.88rem', color: '#1e40af', marginTop: '0.2rem' }}>
            These term proposals are for decision support only. No changes have been applied to the original contract or on-chain state.
          </div>
        </div>
      </div>

      {/* PROPOSED TERMS TABLE */}
      {negData && (
        <div className="card" style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '1.5rem' }}>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
            Recommended Term Adjustments
          </div>
          <div style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1.25rem' }}>
            {negData.negotiation_summary}
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600, color: '#475569' }}>Parameter</th>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600, color: '#475569' }}>Current Value</th>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600, color: '#475569' }}>Proposed Value</th>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600, color: '#475569' }}>Rationale</th>
              </tr>
            </thead>
            <tbody>
              {negData.optimized_terms.map((term, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '1rem', fontWeight: 700, color: '#0f172a', textTransform: 'capitalize' }}>
                    {term.parameter.replace(/_/g, ' ')}
                  </td>
                  <td style={{ padding: '1rem', color: '#64748b' }}>
                    {term.current_value}
                  </td>
                  <td style={{ padding: '1rem', fontWeight: 700, color: '#0284c7' }}>
                    {term.proposed_value}
                  </td>
                  <td style={{ padding: '1rem', color: '#334155', lineHeight: 1.4 }}>
                    {term.reason}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button
              onClick={() => setShowJson(!showJson)}
              className="btn-secondary"
              style={{ fontSize: '0.85rem' }}
            >
              {showJson ? 'Hide Proposed ACTUS JSON' : 'View Proposed ACTUS JSON'}
            </button>
          </div>

          {showJson && (
            <div style={{ marginTop: '1rem', backgroundColor: '#0f172a', color: '#f8fafc', padding: '1.25rem', borderRadius: '10px', fontFamily: 'monospace', fontSize: '0.85rem', overflowX: 'auto' }}>
              <pre style={{ margin: 0 }}>{JSON.stringify(negData.revised_actus_json, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
