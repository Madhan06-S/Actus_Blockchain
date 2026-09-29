import React, { useEffect, useState } from 'react';
import { CheckCircle2, Loader2, Code2, ChevronDown, ChevronUp } from 'lucide-react';

interface AnalysisScreenProps {
  onComplete: () => void;
}

export const AnalysisScreen: React.FC<AnalysisScreenProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [showTechDetails, setShowTechDetails] = useState(false);

  const steps = [
    { label: 'Reading contract document', tech: 'Phase 2: PDF text extraction & validation' },
    { label: 'Checking contract terms', tech: 'Phase 1: FinancialContract model validation' },
    { label: 'Generating ACTUS contract rules', tech: 'Phase 3: ACTUS ANN Data Dictionary translation' },
    { label: 'Calculating expected payment schedule', tech: 'Phase 4 & 5: Event timeline & cash-flow simulation' },
    { label: 'Creating cryptographic contract fingerprint', tech: 'Phase 6: Canonical SHA-256 hash generation' },
    { label: 'Checking recorded activity on MST Blockchain', tech: 'Phase 7: RPC PaymentRecorded logs retrieval' },
    { label: 'Comparing expected vs recorded activity', tech: 'Phase 7: Payment reconciliation engine' },
    { label: 'Evaluating financial status & reconciliation report', tech: 'Phase 8: Financial Risk / Status layer evaluation' },
  ];

  useEffect(() => {
    if (currentStep < steps.length) {
      const timer = setTimeout(() => {
        setCurrentStep((prev) => prev + 1);
      }, 400);
      return () => clearTimeout(timer);
    } else {
      const finishTimer = setTimeout(() => {
        onComplete();
      }, 600);
      return () => clearTimeout(finishTimer);
    }
  }, [currentStep, steps.length, onComplete]);

  return (
    <div style={{ maxWidth: '680px', margin: '3.5rem auto', padding: '0 1.5rem' }} className="animate-fade-in">
      <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2rem', color: '#0f172a', marginBottom: '0.5rem', fontWeight: 700 }}>
          Analyzing Your Contract
        </h1>
        <p style={{ fontSize: '1rem', color: '#475569' }}>
          We're calculating the expected payment schedule and checking it against recorded activity.
        </p>
      </div>

      <div className="card" style={{ padding: '2rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {steps.map((step, index) => {
            const isDone = index < currentStep;
            const isCurrent = index === currentStep;

            return (
              <div
                key={index}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  color: isDone ? '#0f172a' : isCurrent ? '#0284c7' : '#94a3b8',
                  fontWeight: isCurrent ? 600 : 500,
                  fontSize: '0.95rem',
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{ width: 24, display: 'flex', justifyContent: 'center' }}>
                  {isDone ? (
                    <CheckCircle2 size={22} color="#059669" />
                  ) : isCurrent ? (
                    <Loader2 size={20} color="#0284c7" className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
                  ) : (
                    <div style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#cbd5e1' }} />
                  )}
                </div>
                <div style={{ flex: 1 }}>
                  <div>{step.label}</div>
                  {showTechDetails && (
                    <div style={{ fontSize: '0.78rem', color: '#64748b', fontFamily: 'monospace', marginTop: '0.15rem' }}>
                      {step.tech}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
        <button
          onClick={() => setShowTechDetails(!showTechDetails)}
          style={{
            fontSize: '0.85rem',
            color: '#64748b',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            fontWeight: 500,
          }}
        >
          <Code2 size={16} />
          {showTechDetails ? 'Hide technical details' : 'Show technical details'}
          {showTechDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
