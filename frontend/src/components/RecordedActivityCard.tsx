import React, { useState } from 'react';
import { Server, ExternalLink, Copy, Check } from 'lucide-react';
import { DEMO_BLOCKCHAIN_ADDRESS } from '../mock/demoData';

interface RecordedActivityCardProps {
  address?: string;
  blockchainStatus?: string;
  paymentCount?: number;
}

export const RecordedActivityCard: React.FC<RecordedActivityCardProps> = ({
  address = DEMO_BLOCKCHAIN_ADDRESS,
  blockchainStatus = 'COMPLETED',
  paymentCount = 2,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(address);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{ padding: '0.4rem', borderRadius: '6px', backgroundColor: '#ecfdf5', color: '#059669' }}>
            <Server size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>Recorded Activity (Blockchain)</h3>
            <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
              On-chain settlement state recorded on MST Blockchain
            </p>
          </div>
        </div>

        <span
          style={{
            backgroundColor: '#ecfdf5',
            color: '#047857',
            border: '1px solid #a7f3d0',
            borderRadius: '20px',
            padding: '0.3rem 0.75rem',
            fontSize: '0.8rem',
            fontWeight: 700,
          }}
        >
          {blockchainStatus} ON-CHAIN
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div style={{ padding: '0.85rem', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>NETWORK</div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>MST Testnet</div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Chain ID: 91562037</div>
        </div>

        <div style={{ padding: '0.85rem', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>CONTRACT ADDRESS</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.1rem' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 700, fontFamily: 'monospace', color: '#0f172a' }}>
              {address.substring(0, 10)}...{address.substring(address.length - 6)}
            </span>
            <button onClick={handleCopy} style={{ color: '#0284c7' }} title="Copy Address">
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
          </div>
        </div>

        <div style={{ padding: '0.85rem', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>RECORDED PAYMENTS</div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>{paymentCount} Transactions</div>
          <div style={{ fontSize: '0.75rem', color: '#047857' }}>Verified on ledger</div>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <a
          href="https://testnetrpc.mstblockchain.com"
          target="_blank"
          rel="noreferrer"
          className="btn-secondary"
          style={{ textDecoration: 'none', padding: '0.4rem 0.85rem', fontSize: '0.85rem' }}
        >
          View on MST Explorer <ExternalLink size={14} />
        </a>
      </div>
    </div>
  );
};
