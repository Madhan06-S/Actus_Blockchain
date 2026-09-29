import React from 'react';
import type { FinancialContract, RiskStatusResponse, ComparisonItem } from '../types/contract';
import { StatusBadge } from '../components/StatusBadge';
import { ExpectedVsActualCard } from '../components/ExpectedVsActualCard';
import { PaymentTimeline } from '../components/PaymentTimeline';
import { IntegrityCard } from '../components/IntegrityCard';
import { RecordedActivityCard } from '../components/RecordedActivityCard';
import { ContractRulesCard } from '../components/ContractRulesCard';
import { TechnicalDetailsDrawer } from '../components/TechnicalDetailsDrawer';
import { FileText, RefreshCw, HelpCircle } from 'lucide-react';

interface DashboardScreenProps {
  contract: FinancialContract;
  statusData: RiskStatusResponse;
  comparisonItems: ComparisonItem[];
  activeTab: string;
  onRestart: () => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({
  contract,
  statusData,
  comparisonItems,
  activeTab,
  onRestart,
}) => {
  const formatCurrency = (val: string) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(parseFloat(val));
  };

  return (
    <div style={{ padding: '2rem 2.5rem', display: 'flex', flexDirection: 'column', gap: '2rem' }} className="animate-fade-in">
      {/* HEADER BAR */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
          backgroundColor: '#ffffff',
          padding: '1.25rem 1.75rem',
          borderRadius: '14px',
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.05)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '0.6rem', borderRadius: '10px', backgroundColor: '#f0f9ff', color: '#0284c7' }}>
            <FileText size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
              FINANCIAL CONTRACT SUMMARY
            </div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              Annuity Loan ({formatCurrency(contract.principal)})
            </h2>
            <div style={{ fontSize: '0.85rem', color: '#475569', marginTop: '0.15rem' }}>
              10% annual interest • Monthly payments • {contract.start_date} → {contract.maturity_date}
            </div>
          </div>
        </div>

        <button onClick={onRestart} className="btn-secondary" style={{ fontSize: '0.85rem' }}>
          <RefreshCw size={15} /> Upload Another Contract
        </button>
      </div>

      {/* OVERVIEW TAB CONTENT */}
      {(activeTab === 'overview' || activeTab === 'contract') && (
        <>
          {/* PROMINENT STATUS CARD */}
          <div
            className="card"
            style={{
              backgroundColor: statusData.overall_status === 'DEVIATION_DETECTED' ? '#fff1f2' : '#ffffff',
              borderColor: statusData.overall_status === 'DEVIATION_DETECTED' ? '#fecdd3' : '#e2e8f0',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.25rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                  FINANCIAL RECONCILIATION STATUS:
                </span>
                <StatusBadge status={statusData.overall_status} size="lg" />
              </div>

              <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                Evaluated at {new Date(statusData.evaluation_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} UTC
              </div>
            </div>

            {/* PLAIN ENGLISH EXPLANATION BOX */}
            <div
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '10px',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, color: '#0f172a', fontSize: '0.95rem' }}>
                <HelpCircle size={18} color="#0284c7" />
                What happened?
              </div>
              <p style={{ fontSize: '0.92rem', color: '#334155', margin: 0, lineHeight: 1.5 }}>
                The contract schedule expects <strong>{statusData.total_expected_payments} monthly payments</strong> totaling{' '}
                <strong>₹{parseFloat(statusData.total_expected_amount).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</strong>. The recorded activity on MST Blockchain contains{' '}
                <strong>{statusData.matched_payment_count} payments</strong> totaling{' '}
                <strong>₹{parseFloat(statusData.total_actual_paid).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</strong>.
              </p>

              <div style={{ fontSize: '0.88rem', color: '#e11d48', fontWeight: 600, marginTop: '0.25rem' }}>
                Why is this different? {statusData.unpaid_payment_count} expected scheduled payments have not yet been recorded.
              </div>
            </div>
          </div>

          {/* EXPECTED VS ACTUAL CARD */}
          <ExpectedVsActualCard statusData={statusData} />
        </>
      )}

      {/* SCHEDULE & TIMELINE TAB */}
      {(activeTab === 'overview' || activeTab === 'schedule') && (
        <PaymentTimeline comparisonItems={comparisonItems} />
      )}

      {/* RECORDED ACTIVITY TAB */}
      {(activeTab === 'overview' || activeTab === 'activity') && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
          <RecordedActivityCard
            address={statusData.blockchain_contract_address || undefined}
            blockchainStatus={statusData.blockchain_status || 'ACTIVE'}
            paymentCount={statusData.matched_payment_count}
          />
          <ContractRulesCard />
        </div>
      )}

      {/* INTEGRITY TAB */}
      {(activeTab === 'overview' || activeTab === 'integrity') && (
        <>
          <IntegrityCard />
          <TechnicalDetailsDrawer statusData={statusData} />
        </>
      )}
    </div>
  );
};
