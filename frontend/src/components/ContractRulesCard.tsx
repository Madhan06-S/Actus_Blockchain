import React from 'react';
import { FileCode2 } from 'lucide-react';

interface ContractRulesCardProps {
  contractType?: string;
  paymentFrequency?: string;
  expectedEventCount?: number;
}

export const ContractRulesCard: React.FC<ContractRulesCardProps> = ({
  contractType = 'Annuity (ANN)',
  paymentFrequency = 'Monthly',
  expectedEventCount = 50,
}) => {
  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
        <div style={{ padding: '0.4rem', borderRadius: '6px', backgroundColor: '#f0f9ff', color: '#0284c7' }}>
          <FileCode2 size={20} />
        </div>
        <div>
          <h3 style={{ fontSize: '1.1rem', margin: 0 }}>Contract Rules & Logic</h3>
          <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
            Standardized contract rules generating expected payment timeline
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div style={{ padding: '0.85rem', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>CONTRACT TYPE</div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>{contractType}</div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Fixed periodic payment structure</div>
        </div>

        <div style={{ padding: '0.85rem', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>PAYMENT FREQUENCY</div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>{paymentFrequency}</div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Calendar month cycle</div>
        </div>

        <div style={{ padding: '0.85rem', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>EXPECTED EVENTS TIMELINE</div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>{expectedEventCount} Events</div>
          <div style={{ fontSize: '0.75rem', color: '#0284c7' }}>IED, IP, PR, MD timeline</div>
        </div>
      </div>
    </div>
  );
};
