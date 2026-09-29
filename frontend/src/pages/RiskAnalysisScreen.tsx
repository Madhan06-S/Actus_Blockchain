import React, { useState } from 'react';
import { ShieldAlert, Cpu, ChevronDown, ChevronUp, AlertCircle, CheckCircle2 } from 'lucide-react';
import type { FinancialContract, RiskPredictionResponse } from '../types/contract';

interface RiskAnalysisScreenProps {
  contract: FinancialContract;
  riskData: RiskPredictionResponse | null;
}

export const RiskAnalysisScreen: React.FC<RiskAnalysisScreenProps> = ({ contract, riskData }) => {
  const [showInputs, setShowInputs] = useState(false);

  const isAvailable = riskData?.model_available ?? false;
  const category = riskData?.risk_category || 'NOT_AVAILABLE';
  const probPct = riskData?.default_probability_percent ?? null;
  const expLoss = riskData?.expected_loss ?? null;
  const recommendation = riskData?.recommendation || 'MANUAL REVIEW';

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
            <ShieldAlert size={28} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              AI Credit Risk Analysis
            </h2>
            <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.2rem' }}>
              Contract ID: {contract.contract_id} • Evaluated via 22+ quantitative features
            </div>
          </div>
        </div>

        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 1rem',
            borderRadius: '20px',
            fontSize: '0.85rem',
            fontWeight: 600,
            backgroundColor: isAvailable ? '#ecfdf5' : '#fffbeb',
            color: isAvailable ? '#047857' : '#b45309',
            border: `1px solid ${isAvailable ? '#a7f3d0' : '#fde68a'}`,
          }}
        >
          <Cpu size={16} />
          {isAvailable ? 'Trained ML Model Loaded' : 'ML Model Not Configured'}
        </div>
      </div>

      {/* METRICS CARDS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem' }}>
        <div className="card" style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
            Default Probability
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#0f172a', marginTop: '0.4rem' }}>
            {probPct !== null ? `${probPct}%` : 'N/A'}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>
            Model-predicted probability of default
          </div>
        </div>

        <div className="card" style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
            Risk Category
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: category === 'HIGH' ? '#dc2626' : category === 'MEDIUM' ? '#d97706' : '#16a34a', marginTop: '0.4rem' }}>
            {category}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>
            Classification category
          </div>
        </div>

        <div className="card" style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
            Expected Loss
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0f172a', marginTop: '0.4rem' }}>
            {expLoss !== null ? `₹${expLoss.toLocaleString('en-IN')}` : 'N/A'}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>
            Probability × Exposure at default
          </div>
        </div>

        <div className="card" style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
            Recommendation
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#0284c7', marginTop: '0.6rem' }}>
            {recommendation}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>
            Decision support recommendation
          </div>
        </div>
      </div>

      {/* MODEL STATUS / TRANSPARENCY NOTICE */}
      <div
        style={{
          backgroundColor: isAvailable ? '#f0fdf4' : '#fff9eb',
          border: `1px solid ${isAvailable ? '#bbf7d0' : '#fef08a'}`,
          borderRadius: '12px',
          padding: '1.25rem 1.5rem',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '1rem',
        }}
      >
        {isAvailable ? <CheckCircle2 size={24} color="#16a34a" /> : <AlertCircle size={24} color="#d97706" />}
        <div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>
            {isAvailable ? 'Trained Machine Learning Model Active' : 'ML Model Not Configured (Using Prototype Risk Estimator)'}
          </div>
          <div style={{ fontSize: '0.88rem', color: '#475569', marginTop: '0.25rem', lineHeight: 1.5 }}>
            {riskData?.message || 'Quantitative contract attributes have been extracted across principal, annual rate, duration, expected payment schedule, and payment variances.'}
          </div>
        </div>
      </div>

      {/* EXPANDABLE MODEL INPUTS SECTION */}
      <div
        className="card"
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '14px',
          overflow: 'hidden',
        }}
      >
        <button
          onClick={() => setShowInputs(!showInputs)}
          style={{
            width: '100%',
            padding: '1.25rem 1.75rem',
            backgroundColor: '#ffffff',
            border: 'none',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
            textAlign: 'left',
          }}
        >
          <div style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a' }}>
            View Model Inputs ({riskData?.features_used.length || 0} Features Extracted)
          </div>
          {showInputs ? <ChevronUp size={20} color="#64748b" /> : <ChevronDown size={20} color="#64748b" />}
        </button>

        {showInputs && (
          <div style={{ padding: '0 1.75rem 1.5rem 1.75rem', borderTop: '1px solid #f1f5f9' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: '#475569' }}>Feature Name</th>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: '#475569' }}>Value</th>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: '#475569' }}>Description</th>
                </tr>
              </thead>
              <tbody>
                {(riskData?.features_used || []).map((feat, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '0.75rem 1rem', fontFamily: 'monospace', fontWeight: 600, color: '#0284c7' }}>
                      {feat.name}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 700, color: '#0f172a' }}>
                      {String(feat.value)}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: '#64748b' }}>
                      {feat.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
