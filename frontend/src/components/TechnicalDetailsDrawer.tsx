import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Code2 } from 'lucide-react';
import type { RiskStatusResponse } from '../types/contract';
import { DEMO_HASH_INFO } from '../mock/demoData';

interface TechnicalDetailsDrawerProps {
  statusData: RiskStatusResponse;
}

export const TechnicalDetailsDrawer: React.FC<TechnicalDetailsDrawerProps> = ({ statusData }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div
      style={{
        border: '1px dashed #cbd5e1',
        borderRadius: '12px',
        backgroundColor: '#ffffff',
        overflow: 'hidden',
        marginTop: '1rem',
      }}
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '100%',
          padding: '1rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: '#f8fafc',
          color: '#475569',
          fontWeight: 600,
          fontSize: '0.9rem',
          textAlign: 'left',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Code2 size={18} color="#0284c7" />
          Technical Details & Hackathon Judge Inspection Payload
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: '#64748b' }}>
          {isOpen ? 'Collapse' : 'Expand'} {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </button>

      {isOpen && (
        <div style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem', backgroundColor: '#0f172a', color: '#e2e8f0' }} className="animate-fade-in">
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', marginBottom: '0.25rem', textTransform: 'uppercase' }}>
              ACTUS Standard Specification
            </div>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', margin: 0 }}>
              Contract Type: <code>ANN</code> | Calendar Convention: <code>AA</code> | Cycle: <code>P1M</code> | Currency: <code>INR</code>
            </p>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', marginBottom: '0.25rem', textTransform: 'uppercase' }}>
              Canonical SHA-256 Digest (Phase 6)
            </div>
            <pre style={{ fontSize: '0.78rem', backgroundColor: '#1e293b', padding: '0.6rem', borderRadius: '6px', color: '#4ade80', overflowX: 'auto' }}>
              {DEMO_HASH_INFO.backend_sha256_hash}
            </pre>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', marginBottom: '0.25rem', textTransform: 'uppercase' }}>
              Raw Risk Status API Payload (GET /api/v1/contracts/{statusData.contract_id}/status)
            </div>
            <pre style={{ fontSize: '0.78rem', backgroundColor: '#1e293b', padding: '0.8rem', borderRadius: '6px', color: '#f8fafc', overflowX: 'auto', maxHeight: '250px' }}>
              {JSON.stringify(statusData, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
