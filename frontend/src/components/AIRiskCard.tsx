import React from 'react';
import { ShieldAlert, Cpu, HelpCircle } from 'lucide-react';
import type { RiskPredictionResponse } from '../types/contract';

interface AIRiskCardProps {
  riskData: RiskPredictionResponse | null;
  onViewDetails: () => void;
}

export const AIRiskCard: React.FC<AIRiskCardProps> = ({ riskData, onViewDetails }) => {
  const isAvailable = riskData?.model_available ?? false;
  const category = riskData?.risk_category || 'NOT_AVAILABLE';
  const probability = riskData?.default_probability_percent ?? null;
  const expectedLoss = riskData?.expected_loss ?? null;
  const recommendation = riskData?.recommendation || 'MANUAL REVIEW';

  const getCategoryColor = (cat: string) => {
    switch (cat) {
      case 'LOW':
        return { bg: '#ecfdf5', text: '#047857', border: '#a7f3d0' };
      case 'MEDIUM':
        return { bg: '#fffbeb', text: '#b45309', border: '#fde68a' };
      case 'HIGH':
        return { bg: '#fef2f2', text: '#b91c1c', border: '#fecaca' };
      default:
        return { bg: '#f8fafc', text: '#64748b', border: '#e2e8f0' };
    }
  };

  const style = getCategoryColor(category);

  return (
    <div
      className="card"
      style={{
        backgroundColor: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '14px',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
        boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.05)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ padding: '0.5rem', borderRadius: '8px', backgroundColor: '#f0f9ff', color: '#0284c7' }}>
            <ShieldAlert size={22} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              AI Risk Analysis
            </h3>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.1rem' }}>
              Predictive credit risk & default probability model
            </div>
          </div>
        </div>

        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.35rem 0.75rem',
            borderRadius: '20px',
            fontSize: '0.75rem',
            fontWeight: 600,
            backgroundColor: isAvailable ? '#f0fdf4' : '#fef2f2',
            color: isAvailable ? '#166534' : '#991b1b',
            border: `1px solid ${isAvailable ? '#bbf7d0' : '#fecaca'}`,
          }}
        >
          <Cpu size={14} />
          {isAvailable ? 'ML Model Active' : 'ML Model Not Configured'}
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '1rem',
          backgroundColor: '#f8fafc',
          padding: '1.25rem',
          borderRadius: '10px',
          border: '1px solid #f1f5f9',
        }}
      >
        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
            Default Probability
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#0f172a', marginTop: '0.2rem' }}>
            {probability !== null ? `${probability}%` : 'N/A'}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
            Risk Category
          </div>
          <div style={{ marginTop: '0.4rem' }}>
            <span
              style={{
                display: 'inline-block',
                padding: '0.3rem 0.75rem',
                borderRadius: '6px',
                fontSize: '0.85rem',
                fontWeight: 700,
                backgroundColor: style.bg,
                color: style.text,
                border: `1px solid ${style.border}`,
              }}
            >
              {category}
            </span>
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
            Expected Loss
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a', marginTop: '0.2rem' }}>
            {expectedLoss !== null ? `₹${expectedLoss.toLocaleString('en-IN')}` : 'N/A'}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
            Model Recommendation
          </div>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#334155', marginTop: '0.4rem' }}>
            {recommendation}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ fontSize: '0.82rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <HelpCircle size={15} color="#0284c7" />
          {riskData?.estimator_type || 'Prototype risk estimator'}
        </div>
        <button
          onClick={onViewDetails}
          className="btn-secondary"
          style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}
        >
          View Risk Details →
        </button>
      </div>
    </div>
  );
};
