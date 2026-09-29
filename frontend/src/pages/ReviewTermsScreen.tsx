import React, { useState, useEffect } from 'react';
import type { CandidateTerms } from '../types/contract';
import { Edit3, ArrowRight, Info, Loader2, AlertTriangle, RefreshCw } from 'lucide-react';

interface ReviewTermsScreenProps {
  documentId?: string | null;
  fileName?: string | null;
  initialTerms: CandidateTerms | null;
  extractionError?: string | null;
  onConfirm: (confirmedTerms: CandidateTerms) => void;
  onRetry?: () => void;
}

const EMPTY_TERMS: CandidateTerms = {
  principal: '',
  currency: 'INR',
  annual_interest_rate: '',
  payment_frequency: 'MONTHLY',
  start_date: '',
  maturity_date: '',
  contract_role: 'RPA',
  confidence: 0,
};

export const ReviewTermsScreen: React.FC<ReviewTermsScreenProps> = ({
  documentId,
  fileName,
  initialTerms,
  extractionError,
  onConfirm,
  onRetry,
}) => {
  const [terms, setTerms] = useState<CandidateTerms>(initialTerms ?? EMPTY_TERMS);
  const [isEditing, setIsEditing] = useState(false);

  // Sync terms when initialTerms arrive (async extraction)
  useEffect(() => {
    if (initialTerms) {
      setTerms(initialTerms);
    }
  }, [initialTerms]);

  const handleTextChange = (field: keyof CandidateTerms, value: string) => {
    setTerms((prev) => ({ ...prev, [field]: value }));
  };

  const formatCurrency = (val: string) => {
    const num = parseFloat(val);
    return isNaN(num) ? (val || '—') : new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(num);
  };

  const missingFields = [
    !terms.principal && 'Principal',
    !terms.annual_interest_rate && 'Interest Rate',
    !terms.start_date && 'Start Date',
    !terms.maturity_date && 'Maturity Date',
  ].filter(Boolean);

  // — LOADING STATE —
  if (!initialTerms && !extractionError) {
    return (
      <div style={{ maxWidth: '840px', margin: '5rem auto', padding: '0 1.5rem', textAlign: 'center' }}>
        <Loader2 size={40} color="#0284c7" style={{ animation: 'spin 1s linear infinite', marginBottom: '1.25rem' }} />
        <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
          Extracting Contract Terms
        </h2>
        <p style={{ color: '#64748b' }}>Reading your contract document and identifying financial terms…</p>
      </div>
    );
  }

  // — ERROR STATE —
  if (extractionError) {
    return (
      <div style={{ maxWidth: '600px', margin: '5rem auto', padding: '0 1.5rem', textAlign: 'center' }}>
        <div style={{ display: 'inline-flex', padding: '1rem', borderRadius: '50%', backgroundColor: '#fef2f2', marginBottom: '1.25rem' }}>
          <AlertTriangle size={36} color="#dc2626" />
        </div>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.75rem' }}>
          Unable to Extract Contract Terms
        </h2>
        <p style={{ color: '#64748b', marginBottom: '0.5rem' }}>
          {extractionError}
        </p>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '2rem' }}>
          The document may be scanned/image-based or the required financial terms could not be identified.
        </p>
        {onRetry && (
          <button onClick={onRetry} className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
            <RefreshCw size={16} /> Retry Upload
          </button>
        )}
      </div>
    );
  }

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

      {/* Info Banner */}
      <div style={{
        backgroundColor: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: '10px',
        padding: '0.85rem 1.25rem', marginBottom: '1.75rem', display: 'flex',
        alignItems: 'center', justifyContent: 'space-between', gap: '0.6rem',
        fontSize: '0.88rem', color: '#0369a1',
      }}>
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

      {/* Missing fields warning */}
      {missingFields.length > 0 && (
        <div style={{
          backgroundColor: '#fffbeb', border: '1px solid #fde68a', borderRadius: '10px',
          padding: '0.75rem 1.25rem', marginBottom: '1.5rem', fontSize: '0.88rem', color: '#92400e',
          display: 'flex', alignItems: 'center', gap: '0.6rem',
        }}>
          <AlertTriangle size={16} />
          Some fields could not be extracted: <strong>{missingFields.join(', ')}</strong>. Please fill them in before confirming.
        </div>
      )}

      {/* Terms Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        {/* Principal */}
        <div className="card" style={{ borderLeft: `4px solid ${terms.principal ? '#0284c7' : '#f59e0b'}` }}>
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>PRINCIPAL AMOUNT</div>
          {isEditing ? (
            <input type="text" value={terms.principal}
              onChange={(e) => handleTextChange('principal', e.target.value)}
              placeholder="e.g. 500000"
              style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '1.1rem', fontWeight: 700 }} />
          ) : (
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: terms.principal ? '#0f172a' : '#f59e0b' }}>
              {terms.principal ? formatCurrency(terms.principal) : '⚠ Not found'}
            </div>
          )}
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.25rem' }}>Currency: {terms.currency || 'INR'}</div>
        </div>

        {/* Interest Rate */}
        <div className="card" style={{ borderLeft: `4px solid ${terms.annual_interest_rate ? '#0284c7' : '#f59e0b'}` }}>
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>ANNUAL INTEREST RATE</div>
          {isEditing ? (
            <input type="text" value={terms.annual_interest_rate}
              onChange={(e) => handleTextChange('annual_interest_rate', e.target.value)}
              placeholder="e.g. 12.5"
              style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '1.1rem', fontWeight: 700 }} />
          ) : (
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: terms.annual_interest_rate ? '#0f172a' : '#f59e0b' }}>
              {terms.annual_interest_rate ? `${terms.annual_interest_rate}% per annum` : '⚠ Not found'}
            </div>
          )}
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.25rem' }}>Fixed Rate</div>
        </div>

        {/* Payment Frequency */}
        <div className="card" style={{ borderLeft: '4px solid #0284c7' }}>
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>PAYMENT FREQUENCY</div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#0f172a' }}>{terms.payment_frequency || 'MONTHLY'}</div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.25rem' }}>Calendar Month Amortization</div>
        </div>

        {/* Start Date */}
        <div className="card" style={{ borderLeft: `4px solid ${terms.start_date ? '#94a3b8' : '#f59e0b'}` }}>
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>START DATE</div>
          {isEditing ? (
            <input type="date" value={terms.start_date}
              onChange={(e) => handleTextChange('start_date', e.target.value)}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '1rem', fontWeight: 700 }} />
          ) : (
            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: terms.start_date ? '#0f172a' : '#f59e0b' }}>
              {terms.start_date || '⚠ Not found'}
            </div>
          )}
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.25rem' }}>Initial Disbursement</div>
        </div>

        {/* Maturity Date */}
        <div className="card" style={{ borderLeft: `4px solid ${terms.maturity_date ? '#94a3b8' : '#f59e0b'}` }}>
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>MATURITY DATE</div>
          {isEditing ? (
            <input type="date" value={terms.maturity_date}
              onChange={(e) => handleTextChange('maturity_date', e.target.value)}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '1rem', fontWeight: 700 }} />
          ) : (
            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: terms.maturity_date ? '#0f172a' : '#f59e0b' }}>
              {terms.maturity_date || '⚠ Not found'}
            </div>
          )}
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.25rem' }}>Final Maturity</div>
        </div>

        {/* Contract Role */}
        <div className="card" style={{ borderLeft: '4px solid #94a3b8' }}>
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>CONTRACT ROLE</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#0f172a' }}>
            {terms.contract_role === 'RPA' ? 'Lender (Real Asset)' : 'Borrower'}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.25rem' }}>Off-chain counterpart</div>
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid #e2e8f0', paddingTop: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={() => setIsEditing(!isEditing)} className="btn-secondary">
            <Edit3 size={16} /> {isEditing ? 'Save Edits' : 'Edit Details'}
          </button>
          {onRetry && (
            <button onClick={onRetry} style={{ fontSize: '0.85rem', color: '#64748b', display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontWeight: 500 }}>
              <RefreshCw size={14} /> Upload Different PDF
            </button>
          )}
        </div>

        <button
          onClick={() => onConfirm(terms)}
          className="btn-primary"
          disabled={missingFields.length > 0 && !isEditing}
          style={{ padding: '0.85rem 2rem', fontSize: '1rem', opacity: (missingFields.length > 0 && !isEditing) ? 0.5 : 1 }}
        >
          Everything Looks Correct → Analyze <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
};
