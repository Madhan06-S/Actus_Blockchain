import React, { useState } from 'react';
import { ShieldCheck, ShieldAlert, Copy, Check } from 'lucide-react';
import { DEMO_HASH_INFO } from '../mock/demoData';

interface IntegrityCardProps {
  hashInfo?: typeof DEMO_HASH_INFO;
}

export const IntegrityCard: React.FC<IntegrityCardProps> = ({ hashInfo = DEMO_HASH_INFO }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(hashInfo.backend_sha256_hash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isMatch = hashInfo.is_match;

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{ padding: '0.4rem', borderRadius: '6px', backgroundColor: isMatch ? '#ecfdf5' : '#fff1f2', color: isMatch ? '#059669' : '#e11d48' }}>
            {isMatch ? <ShieldCheck size={20} /> : <ShieldAlert size={20} />}
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>Contract Integrity</h3>
            <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
              Cryptographic fingerprint comparison between contract and blockchain record
            </p>
          </div>
        </div>

        <span
          style={{
            backgroundColor: isMatch ? '#ecfdf5' : '#fff1f2',
            color: isMatch ? '#047857' : '#e11d48',
            border: `1px solid ${isMatch ? '#a7f3d0' : '#fecdd3'}`,
            borderRadius: '20px',
            padding: '0.3rem 0.75rem',
            fontSize: '0.8rem',
            fontWeight: 700,
          }}
        >
          {isMatch ? '✓ Fingerprints Match' : '⚠ Fingerprints Do Not Match'}
        </span>
      </div>

      <p style={{ fontSize: '0.9rem', color: '#475569', backgroundColor: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #e2e8f0', margin: 0 }}>
        We generate a unique fingerprint of the contract and compare it with the fingerprint recorded on the blockchain.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.85rem 1rem', backgroundColor: '#ffffff' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', marginBottom: '0.3rem' }}>
            BACKEND SHA-256 FINGERPRINT
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
            <span style={{ fontFamily: 'monospace', fontSize: '0.82rem', color: '#0f172a', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {hashInfo.backend_sha256_hash.substring(0, 24)}...
            </span>
            <button onClick={handleCopy} style={{ padding: '0.25rem', color: '#0284c7' }} title="Copy hash">
              {copied ? <Check size={16} /> : <Copy size={16} />}
            </button>
          </div>
        </div>

        <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.85rem 1rem', backgroundColor: '#ffffff' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', marginBottom: '0.3rem' }}>
            BLOCKCHAIN RECORDED FINGERPRINT
          </div>
          <div style={{ fontFamily: 'monospace', fontSize: '0.82rem', color: '#0f172a', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {hashInfo.blockchain_actus_hash.substring(0, 24)}...
          </div>
        </div>
      </div>
    </div>
  );
};
