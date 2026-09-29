import React, { useState } from 'react';
import { TrendingUp, Zap } from 'lucide-react';
import type { FinancialContract, StressTestResponse } from '../types/contract';
import { contractsApi } from '../api/contractsApi';

interface StressTestScreenProps {
  contract: FinancialContract;
}

export const StressTestScreen: React.FC<StressTestScreenProps> = ({ contract }) => {
  const [rateShock, setRateShock] = useState<number>(3.0);
  const [loading, setLoading] = useState<boolean>(false);
  const [stressData, setStressData] = useState<StressTestResponse | null>(null);

  const handleRunStressTest = async (shockVal: number) => {
    setLoading(true);
    try {
      const res = await contractsApi.runStressTest(contract.contract_id, {
        rate_shock_percent: shockVal,
        scenario_description: `Interest rate increase of +${shockVal.toFixed(1)}%`,
      }, contract);
      setStressData(res);
    } catch (err) {
      console.warn('Stress test API fallback:', err);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    handleRunStressTest(rateShock);
  }, []);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);
  };

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
            <TrendingUp size={28} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              Scenario Stress Testing
            </h2>
            <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.2rem' }}>
              Simulate interest rate shocks on ACTUS cash flows without modifying original contract
            </div>
          </div>
        </div>
      </div>

      {/* CONTROLS CARD */}
      <div className="card" style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '1.5rem' }}>
        <div style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a', marginBottom: '1rem' }}>
          Configure What-If Scenario
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '240px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '0.5rem' }}>
              Interest Rate Shock (+%)
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <input
                type="range"
                min="0.5"
                max="10.0"
                step="0.5"
                value={rateShock}
                onChange={(e) => setRateShock(parseFloat(e.target.value))}
                style={{ flex: 1, accentColor: '#0284c7' }}
              />
              <span style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0284c7', minWidth: '60px' }}>
                +{rateShock.toFixed(1)}%
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {[1.0, 2.0, 3.0, 5.0].map((val) => (
              <button
                key={val}
                onClick={() => {
                  setRateShock(val);
                  handleRunStressTest(val);
                }}
                className={rateShock === val ? 'btn-primary' : 'btn-secondary'}
                style={{ fontSize: '0.85rem', padding: '0.4rem 0.85rem' }}
              >
                +{val.toFixed(1)}%
              </button>
            ))}
          </div>

          <button
            onClick={() => handleRunStressTest(rateShock)}
            className="btn-primary"
            disabled={loading}
            style={{ fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <Zap size={16} />
            {loading ? 'Simulating...' : 'Run Stress Test'}
          </button>
        </div>
      </div>

      {/* COMPARISON CARDS */}
      {stressData && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
            {/* BASE CASE */}
            <div className="card" style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '1.5rem' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                BASE CASE (CURRENT)
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f172a' }}>
                {stressData.base_case.annual_interest_rate}% Interest
              </div>
              <div style={{ marginTop: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem' }}>
                  <span style={{ color: '#64748b' }}>Monthly Payment:</span>
                  <span style={{ fontWeight: 700, color: '#0f172a' }}>{formatCurrency(stressData.base_case.monthly_payment)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem' }}>
                  <span style={{ color: '#64748b' }}>Total Interest:</span>
                  <span style={{ fontWeight: 700, color: '#0f172a' }}>{formatCurrency(stressData.base_case.total_interest)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem' }}>
                  <span style={{ color: '#64748b' }}>Total Repayment:</span>
                  <span style={{ fontWeight: 700, color: '#0f172a' }}>{formatCurrency(stressData.base_case.total_repayment)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Risk Category:</span>
                  <span style={{ fontWeight: 700, color: '#16a34a' }}>{stressData.base_case.risk_category}</span>
                </div>
              </div>
            </div>

            {/* STRESSED CASE */}
            <div className="card" style={{ backgroundColor: '#fffbf5', border: '1px solid #fed7aa', borderRadius: '14px', padding: '1.5rem' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#c2410c', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                STRESSED CASE (+{stressData.difference.rate_shock_percent}%)
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#9a3412' }}>
                {stressData.stressed_case.annual_interest_rate}% Interest
              </div>
              <div style={{ marginTop: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #ffedd5', paddingBottom: '0.5rem' }}>
                  <span style={{ color: '#9a3412' }}>Monthly Payment:</span>
                  <span style={{ fontWeight: 700, color: '#9a3412' }}>{formatCurrency(stressData.stressed_case.monthly_payment)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #ffedd5', paddingBottom: '0.5rem' }}>
                  <span style={{ color: '#9a3412' }}>Total Interest:</span>
                  <span style={{ fontWeight: 700, color: '#9a3412' }}>{formatCurrency(stressData.stressed_case.total_interest)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #ffedd5', paddingBottom: '0.5rem' }}>
                  <span style={{ color: '#9a3412' }}>Total Repayment:</span>
                  <span style={{ fontWeight: 700, color: '#9a3412' }}>{formatCurrency(stressData.stressed_case.total_repayment)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#9a3412' }}>Stressed Risk Category:</span>
                  <span style={{ fontWeight: 700, color: '#dc2626' }}>{stressData.stressed_case.risk_category}</span>
                </div>
              </div>
            </div>
          </div>

          {/* VARIANCE & RISK IMPACT SUMMARY */}
          <div className="card" style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '1.5rem' }}>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.75rem' }}>
              Financial Variance & Risk Impact
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
              <div style={{ backgroundColor: '#f8fafc', padding: '1rem', borderRadius: '10px' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>ADDITIONAL MONTHLY PAYMENT</div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#c2410c', marginTop: '0.25rem' }}>
                  +{formatCurrency(stressData.difference.additional_monthly_payment)}
                </div>
              </div>

              <div style={{ backgroundColor: '#f8fafc', padding: '1rem', borderRadius: '10px' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>ADDITIONAL TOTAL INTEREST</div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#c2410c', marginTop: '0.25rem' }}>
                  +{formatCurrency(stressData.difference.additional_interest)} ({stressData.difference.percentage_increase_in_interest}% ↑)
                </div>
              </div>

              <div style={{ backgroundColor: '#f8fafc', padding: '1rem', borderRadius: '10px' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>TOTAL REPAYMENT VARIANCE</div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#c2410c', marginTop: '0.25rem' }}>
                  +{formatCurrency(stressData.difference.additional_total_repayment)}
                </div>
              </div>
            </div>

            <p style={{ fontSize: '0.9rem', color: '#475569', margin: 0, lineHeight: 1.5 }}>
              {stressData.risk_impact.summary}
            </p>
          </div>
        </>
      )}
    </div>
  );
};
