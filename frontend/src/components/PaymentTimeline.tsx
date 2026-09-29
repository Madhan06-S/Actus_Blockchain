import React, { useState } from 'react';
import type { ComparisonItem } from '../types/contract';
import { Calendar, CheckCircle2, Clock, Zap, ExternalLink, Loader2 } from 'lucide-react';
import { contractsApi } from '../api/contractsApi';

interface PaymentTimelineProps {
  comparisonItems: ComparisonItem[];
  currency?: string;
  onPaymentRecorded?: (updatedItems: ComparisonItem[], paidAmount: number, txHash: string) => void;
}

export const PaymentTimeline: React.FC<PaymentTimelineProps> = ({ comparisonItems, currency = 'INR', onPaymentRecorded }) => {
  const [filter, setFilter] = useState<'ALL' | 'RECORDED' | 'UNPAID'>('ALL');
  const [items, setItems] = useState<ComparisonItem[]>(comparisonItems);
  const [payingIndex, setPayingIndex] = useState<number | null>(null);
  const [lastTx, setLastTx] = useState<{ txHash: string; blockNumber: number; amount: number; explorerUrl: string } | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Sync if prop changes externally
  React.useEffect(() => {
    setItems(comparisonItems);
  }, [comparisonItems]);

  const formatCurrency = (val: string | number) => {
    const num = typeof val === 'string' ? parseFloat(val) : val;
    const curr = (currency || 'INR').toUpperCase();
    const locale = curr === 'INR' ? 'en-IN' : 'en-US';
    return new Intl.NumberFormat(locale, { style: 'currency', currency: curr, maximumFractionDigits: 2 }).format(num);
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const handlePayInstallment = async (itemIndex: number, expectedAmount: string) => {
    try {
      setPayingIndex(itemIndex);
      setErrorMsg(null);
      const amountNum = parseFloat(expectedAmount) || 0;

      // Real live transaction on MST Blockchain Testnet
      const res = await contractsApi.recordPayment(amountNum);

      const nowIso = new Date().toISOString();
      const updated = [...items];
      updated[itemIndex] = {
        ...updated[itemIndex],
        status: 'MATCHED',
        actual_payment: {
          payment_id: `pay-${Date.now()}`,
          transaction_hash: res.transaction_hash,
          block_number: res.block_number,
          timestamp: nowIso,
          payer: '0xA235391d02220A619C472ac9A84295C47E7A4f49',
          payee: res.contract_address,
          amount: String(amountNum),
          payment_index: itemIndex + 1,
        },
      };

      setItems(updated);
      setLastTx({
        txHash: res.transaction_hash,
        blockNumber: res.block_number,
        amount: amountNum,
        explorerUrl: res.explorer_url,
      });

      if (onPaymentRecorded) {
        onPaymentRecorded(updated, amountNum, res.transaction_hash);
      }
    } catch (err: unknown) {
      console.error('Payment error:', err);
      const msg = err instanceof Error ? err.message : 'Payment failed';
      setErrorMsg(`Blockchain Transaction Failed: ${msg}`);
    } finally {
      setPayingIndex(null);
    }
  };

  const filteredItems = items.filter((item) => {
    if (filter === 'RECORDED') return item.actual_payment !== null;
    if (filter === 'UNPAID') return item.actual_payment === null;
    return true;
  });

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* HEADER & FILTERS */}
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
              cursor: 'pointer',
              border: 'none',
            }}
          >
            All Items ({items.length})
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
              cursor: 'pointer',
              border: 'none',
            }}
          >
            Recorded ({items.filter((i) => i.actual_payment !== null).length})
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
              cursor: 'pointer',
              border: 'none',
            }}
          >
            Unpaid ({items.filter((i) => i.actual_payment === null).length})
          </button>
        </div>
      </div>

      {/* SUCCESS BANNER WHEN PAYMENT IS BROADCAST */}
      {lastTx && (
        <div
          style={{
            backgroundColor: '#ecfdf5',
            border: '1px solid #a7f3d0',
            borderRadius: '8px',
            padding: '0.85rem 1.1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <CheckCircle2 size={20} color="#059669" />
            <div>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#065f46' }}>
                Payment of {formatCurrency(lastTx.amount)} Successfully Confirmed on MST Blockchain!
              </div>
              <div style={{ fontSize: '0.8rem', color: '#047857' }}>
                Confirmed in Block #{lastTx.blockNumber} • TX: {lastTx.txHash.substring(0, 18)}...
              </div>
            </div>
          </div>
          <a
            href={lastTx.explorerUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.4rem 0.8rem',
              backgroundColor: '#059669',
              color: '#ffffff',
              borderRadius: '6px',
              fontSize: '0.8rem',
              fontWeight: 600,
              textDecoration: 'none',
            }}
          >
            View on MSTScan <ExternalLink size={14} />
          </a>
        </div>
      )}

      {/* ERROR BANNER IF ANY */}
      {errorMsg && (
        <div
          style={{
            backgroundColor: '#fff1f2',
            border: '1px solid #fecdd3',
            borderRadius: '8px',
            padding: '0.75rem 1rem',
            color: '#be123c',
            fontSize: '0.85rem',
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* TIMELINE LIST */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '520px', overflowY: 'auto', paddingRight: '0.5rem' }}>
        {filteredItems.map((item, index) => {
          const originalIndex = items.findIndex((orig) => orig.item_id === item.item_id || (orig.expected_date === item.expected_date && orig.expected_amount === item.expected_amount));
          const actualIndex = originalIndex >= 0 ? originalIndex : index;
          const isRecorded = item.actual_payment !== null;
          const isPaying = payingIndex === actualIndex;

          return (
            <div
              key={item.item_id || index}
              style={{
                display: 'grid',
                gridTemplateColumns: 'minmax(180px, 1fr) auto minmax(260px, 1.3fr)',
                gap: '1rem',
                alignItems: 'center',
                backgroundColor: isRecorded ? '#f8fafc' : '#ffffff',
                border: `1px solid ${isRecorded ? '#cbd5e1' : '#e2e8f0'}`,
                borderRadius: '10px',
                padding: '0.85rem 1.1rem',
                boxShadow: isPaying ? '0 0 0 2px #0284c7' : 'none',
                transition: 'all 0.2s ease',
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

              {/* RECORDED SIDE / ACTION BUTTON */}
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
                    <a
                      href={`https://testnet.mstscan.com/tx/${item.actual_payment.transaction_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        fontSize: '0.75rem',
                        color: '#0284c7',
                        fontFamily: 'monospace',
                        marginTop: '0.15rem',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        textDecoration: 'underline',
                      }}
                    >
                      Tx: {item.actual_payment.transaction_hash.substring(0, 14)}... <ExternalLink size={11} />
                    </a>
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                    <span style={{ fontStyle: 'italic', color: '#94a3b8', fontSize: '0.82rem' }}>
                      Pending
                    </span>
                    <button
                      onClick={() => handlePayInstallment(actualIndex, item.expected_amount)}
                      disabled={isPaying || payingIndex !== null}
                      style={{
                        padding: '0.45rem 0.9rem',
                        backgroundColor: '#0284c7',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: isPaying || payingIndex !== null ? 'not-allowed' : 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.1)',
                        opacity: isPaying || payingIndex !== null ? 0.7 : 1,
                        transition: 'all 0.2s',
                      }}
                    >
                      {isPaying ? (
                        <>
                          <Loader2 size={13} className="animate-spin" /> Paying on MST...
                        </>
                      ) : (
                        <>
                          <Zap size={13} /> Pay {formatCurrency(item.expected_amount)}
                        </>
                      )}
                    </button>
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
