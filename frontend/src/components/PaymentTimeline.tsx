import React, { useState } from 'react';
import type { ComparisonItem } from '../types/contract';
import { Calendar, CheckCircle2, Clock } from 'lucide-react';

interface PaymentTimelineProps {
  comparisonItems: ComparisonItem[];
}

export const PaymentTimeline: React.FC<PaymentTimelineProps> = ({ comparisonItems }) => {
  const [filter, setFilter] = useState<'ALL' | 'RECORDED' | 'UNPAID'>('ALL');

  const formatCurrency = (val: string) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(parseFloat(val));
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const filteredItems = comparisonItems.filter((item) => {
    if (filter === 'RECORDED') return item.actual_payment !== null;
    if (filter === 'UNPAID') return item.actual_payment === null;
    return true;
  });

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{ padding: '0.4rem', borderRadius: '6px', backgroundColor: '#f0f9ff', color: '#0284c7' }}>
            <Calendar size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>Dual-Layer Payment Timeline</h3>
            <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
              Aligning contract expected schedule with actual recorded payments
            </p>
          </div>
        </div>

        {/* Filter buttons */}
        <div style={{ display: 'flex', gap: '0.5rem', backgroundColor: '#f1f5f9', padding: '0.25rem', borderRadius: '8px' }}>
          <button
            onClick={() => setFilter('ALL')}
            style={{
              padding: '0.35rem 0.75rem',
              fontSize: '0.8rem',
              fontWeight: filter === 'ALL' ? 600 : 500,
              borderRadius: '6px',
              backgroundColor: filter === 'ALL' ? '#ffffff' : 'transparent',
              color: filter === 'ALL' ? '#0f172a' : '#64748b',
              boxShadow: filter === 'ALL' ? '0 1px 2px 0 rgb(0 0 0 / 0.05)' : 'none',
            }}
          >
            All Items ({comparisonItems.length})
          </button>
          <button
            onClick={() => setFilter('RECORDED')}
            style={{
              padding: '0.35rem 0.75rem',
              fontSize: '0.8rem',
              fontWeight: filter === 'RECORDED' ? 600 : 500,
              borderRadius: '6px',
              backgroundColor: filter === 'RECORDED' ? '#ffffff' : 'transparent',
              color: filter === 'RECORDED' ? '#0f172a' : '#64748b',
              boxShadow: filter === 'RECORDED' ? '0 1px 2px 0 rgb(0 0 0 / 0.05)' : 'none',
            }}
          >
            Recorded ({comparisonItems.filter(i => i.actual_payment !== null).length})
          </button>
          <button
            onClick={() => setFilter('UNPAID')}
            style={{
              padding: '0.35rem 0.75rem',
              fontSize: '0.8rem',
              fontWeight: filter === 'UNPAID' ? 600 : 500,
              borderRadius: '6px',
              backgroundColor: filter === 'UNPAID' ? '#ffffff' : 'transparent',
              color: filter === 'UNPAID' ? '#0f172a' : '#64748b',
              boxShadow: filter === 'UNPAID' ? '0 1px 2px 0 rgb(0 0 0 / 0.05)' : 'none',
            }}
          >
            Unpaid ({comparisonItems.filter(i => i.actual_payment === null).length})
          </button>
        </div>
      </div>

      {/* TIMELINE LIST */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '520px', overflowY: 'auto', paddingRight: '0.5rem' }}>
        {filteredItems.map((item, index) => {
          const isRecorded = item.actual_payment !== null;

          return (
            <div
              key={item.item_id || index}
              style={{
                display: 'grid',
                gridTemplateColumns: 'minmax(180px, 1fr) auto minmax(220px, 1.2fr)',
                gap: '1rem',
                alignItems: 'center',
                backgroundColor: isRecorded ? '#f8fafc' : '#ffffff',
                border: `1px solid ${isRecorded ? '#cbd5e1' : '#e2e8f0'}`,
                borderRadius: '10px',
                padding: '0.85rem 1.1rem',
              }}
            >
              {/* EXPECTED SIDE */}
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#0284c7', textTransform: 'uppercase', marginBottom: '0.2rem' }}>
                  EXPECTED ({item.expected_event_type})
                </div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a' }}>
                  {formatCurrency(item.expected_amount)}
                </div>
                <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                  Due: {formatDate(item.expected_date)}
                </div>
              </div>

              {/* STATUS INDICATOR CONNECTOR */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.2rem' }}>
                {isRecorded ? (
                  <span
                    style={{
                      backgroundColor: '#ecfdf5',
                      color: '#059669',
                      border: '1px solid #a7f3d0',
                      borderRadius: '12px',
                      padding: '0.2rem 0.6rem',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                    }}
                  >
                    <CheckCircle2 size={12} />
                    Recorded
                  </span>
                ) : (
                  <span
                    style={{
                      backgroundColor: '#f1f5f9',
                      color: '#64748b',
                      border: '1px solid #cbd5e1',
                      borderRadius: '12px',
                      padding: '0.2rem 0.6rem',
                      fontSize: '0.75rem',
                      fontWeight: 500,
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                    }}
                  >
                    <Clock size={12} />
                    Unpaid
                  </span>
                )}
              </div>

              {/* RECORDED SIDE */}
              <div>
                {isRecorded && item.actual_payment ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#059669', textTransform: 'uppercase', marginBottom: '0.2rem' }}>
                      BLOCKCHAIN RECORDED
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a' }}>
                      {formatCurrency(item.actual_payment.amount)}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                      Recorded: {formatDate(item.actual_payment.timestamp)}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#0284c7', fontFamily: 'monospace', marginTop: '0.15rem' }}>
                      Tx: {item.actual_payment.transaction_hash.substring(0, 14)}...
                    </div>
                  </div>
                ) : (
                  <div style={{ fontStyle: 'italic', color: '#94a3b8', fontSize: '0.85rem' }}>
                    No payment recorded on blockchain yet
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
