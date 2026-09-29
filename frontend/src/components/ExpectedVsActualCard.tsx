import React from 'react';
import type { RiskStatusResponse } from '../types/contract';
import { ArrowRightLeft, FileSpreadsheet, Server } from 'lucide-react';

interface ExpectedVsActualCardProps {
  statusData: RiskStatusResponse;
}

export const ExpectedVsActualCard: React.FC<ExpectedVsActualCardProps> = ({ statusData }) => {
  const formatCurrency = (val: string | number) => {
    const num = typeof val === 'string' ? parseFloat(val) : val;
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(num);
  };

  const expectedVal = parseFloat(statusData.total_expected_amount);
  const actualVal = parseFloat(statusData.total_actual_paid);
  const varianceVal = parseFloat(statusData.net_amount_variance);

  const percentagePaid = Math.min(100, Math.round((actualVal / expectedVal) * 100));

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{ padding: '0.4rem', borderRadius: '6px', backgroundColor: '#f0f9ff', color: '#0284c7' }}>
            <ArrowRightLeft size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>Payment Schedule Comparison</h3>
            <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
              Comparing expected contract schedule with recorded blockchain activity
            </p>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
        {/* EXPECTED CARD */}
        <div
          style={{
            backgroundColor: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '12px',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0284c7', fontWeight: 600, fontSize: '0.9rem' }}>
            <FileSpreadsheet size={18} />
            EXPECTED SCHEDULE
          </div>
          <div>
            <span style={{ fontSize: '1.6rem', fontWeight: 700, color: '#0f172a' }}>
              {formatCurrency(expectedVal)}
            </span>
            <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
              Total across {statusData.total_expected_payments} scheduled payments
            </p>
          </div>
          <div style={{ fontSize: '0.8rem', color: '#475569', backgroundColor: '#ffffff', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
            Contract Principal + Interest Schedule
          </div>
        </div>

        {/* ACTUAL BLOCKCHAIN CARD */}
        <div
          style={{
            backgroundColor: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '12px',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#059669', fontWeight: 600, fontSize: '0.9rem' }}>
            <Server size={18} />
            RECORDED ACTIVITY
          </div>
          <div>
            <span style={{ fontSize: '1.6rem', fontWeight: 700, color: '#0f172a' }}>
              {formatCurrency(actualVal)}
            </span>
            <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
              Total across {statusData.matched_payment_count} recorded payments
            </p>
          </div>
          <div style={{ fontSize: '0.8rem', color: '#047857', backgroundColor: '#ecfdf5', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #a7f3d0' }}>
            Recorded on MST Blockchain
          </div>
        </div>

        {/* VARIANCE CARD */}
        <div
          style={{
            backgroundColor: varianceVal < 0 ? '#fff1f2' : '#ecfdf5',
            border: `1px solid ${varianceVal < 0 ? '#fecdd3' : '#a7f3d0'}`,
            borderRadius: '12px',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ color: varianceVal < 0 ? '#e11d48' : '#059669', fontWeight: 600, fontSize: '0.9rem' }}>
            NET DIFFERENCE
          </div>
          <div>
            <span style={{ fontSize: '1.6rem', fontWeight: 700, color: varianceVal < 0 ? '#e11d48' : '#059669' }}>
              {formatCurrency(varianceVal)}
            </span>
            <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
              {statusData.unpaid_payment_count} scheduled payment(s) remaining
            </p>
          </div>
          <div style={{ fontSize: '0.8rem', color: varianceVal < 0 ? '#9f1239' : '#047857', fontWeight: 500 }}>
            {varianceVal < 0 ? 'Less paid than expected schedule' : 'Exact or surplus paid'}
          </div>
        </div>
      </div>

      {/* VISUAL PROGRESS BAR */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '0.4rem' }}>
          <span>Schedule Reconciliation Progress</span>
          <span>{percentagePaid}% Settled</span>
        </div>
        <div style={{ height: '10px', backgroundColor: '#e2e8f0', borderRadius: '5px', overflow: 'hidden', display: 'flex' }}>
          <div style={{ width: `${percentagePaid}%`, backgroundColor: '#059669', transition: 'width 0.4s ease' }}></div>
          <div style={{ width: `${100 - percentagePaid}%`, backgroundColor: '#f43f5e', opacity: 0.3 }}></div>
        </div>
      </div>
    </div>
  );
};
