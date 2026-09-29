import React, { useState } from 'react';
import type { CandidateTerms } from '../types/contract';
import { Edit3, ArrowRight, Info } from 'lucide-react';

interface ReviewTermsScreenProps {
  documentId?: string | null;
  fileName?: string | null;
  initialTerms: CandidateTerms;
  onConfirm: (confirmedTerms: CandidateTerms) => void;
}

export const ReviewTermsScreen: React.FC<ReviewTermsScreenProps> = ({ documentId, fileName, initialTerms, onConfirm }) => {
  const [terms, setTerms] = useState<CandidateTerms>(initialTerms);
  const [isEditing, setIsEditing] = useState(false);

  React.useEffect(() => {
    setTerms(initialTerms);
  }, [initialTerms]);

  const handleTextChange = (field: keyof CandidateTerms, value: string) => {
    setTerms((prev) => ({ ...prev, [field]: value }));
  };

  const formatCurrency = (val: string) => {
    const num = parseFloat(val);
    return isNaN(num) ? val : new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(num);
  };

  return (
    <div style={{ maxWidth: '840px', margin: '2.5rem auto', padding: '0 1.5rem' }} className="animate-fade-in">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', color: '#0f172a', marginBottom: '0.5rem', fontWeight: 700 }}>
          Check Your Contract Details
        </h1>
        <p style={{ fontSize: '1rem', color: '#475569' }}>
          We found these details in your PDF. Please check them before we calculate the payment schedule.
        </p>
      </div>

      <div
        style={{
          backgroundColor: '#f0f9ff',
          border: '1px solid #bae6fd',
          borderRadius: '10px',
          padding: '0.85rem 1.25rem',
          marginBottom: '1.75rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '0.6rem',
          fontSize: '0.88rem',
          color: '#0369a1',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <Info size={18} />
          Extracted terms from contract document {fileName ? `(${fileName})` : ''}. Please verify below.
        </div>
        {documentId && (
          <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', backgroundColor: '#ffffff', padding: '0.2rem 0.5rem', borderRadius: '4px', border: '1px solid #bae6fd' }}>
            ID: {documentId.substring(0, 13)}...
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        {/* Principal Card */}
        <div className="card" style={{ borderLeft: '4px solid #0284c7' }}>
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>
            PRINCIPAL AMOUNT
          </div>
          {isEditing ? (
            <input
              type="text"
              value={terms.principal}
              onChange={(e) => handleTextChange('principal', e.target.value)}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '1.1rem', fontWeight: 700 }}
            />
          ) : (
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a' }}>
              {formatCurrency(terms.principal)}
            </div>
          )}
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.25rem' }}>Currency: INR</div>
        </div>

        {/* Interest Rate Card */}
        <div className="card" style={{ borderLeft: '4px solid #0284c7' }}>
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>
            ANNUAL INTEREST RATE
          </div>
          {isEditing ? (
            <input
              type="text"
              value={terms.annual_interest_rate}
              onChange={(e) => handleTextChange('annual_interest_rate', e.target.value)}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '1.1rem', fontWeight: 700 }}
            />
          ) : (
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a' }}>
              {terms.annual_interest_rate}% per annum
            </div>
          )}
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.25rem' }}>Fixed Rate</div>
        </div>

        {/* Payment Frequency */}
        <div className="card" style={{ borderLeft: '4px solid #0284c7' }}>
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>
            PAYMENT FREQUENCY
          </div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#0f172a' }}>
            {terms.payment_frequency}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.25rem' }}>Calendar Month Amortization</div>
        </div>

        {/* Start Date */}
        <div className="card" style={{ borderLeft: '4px solid #94a3b8' }}>
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>
            START DATE
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#0f172a' }}>
            {terms.start_date}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.25rem' }}>Initial Disbursement</div>
        </div>

        {/* Maturity Date */}
        <div className="card" style={{ borderLeft: '4px solid #94a3b8' }}>
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>
            MATURITY DATE
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#0f172a' }}>
            {terms.maturity_date}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.25rem' }}>Final Maturity</div>
        </div>

        {/* Contract Role */}
        <div className="card" style={{ borderLeft: '4px solid #94a3b8' }}>
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>
            CONTRACT ROLE
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#0f172a' }}>
            {terms.contract_role === 'RPA' ? 'Lender (Real Asset)' : 'Borrower'}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.25rem' }}>Off-chain counterpart</div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid #e2e8f0', paddingTop: '1.5rem' }}>
        <button
          onClick={() => setIsEditing(!isEditing)}
          className="btn-secondary"
        >
          <Edit3 size={16} /> {isEditing ? 'Save Edits' : 'Edit Details'}
        </button>

        <button
          onClick={() => onConfirm(terms)}
          className="btn-primary"
          style={{ padding: '0.85rem 2rem', fontSize: '1rem' }}
        >
          Everything Looks Correct → Analyze <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
};
