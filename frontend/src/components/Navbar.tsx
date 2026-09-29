import React from 'react';
import { Shield, Server } from 'lucide-react';

export const Navbar: React.FC = () => {
  return (
    <header
      style={{
        backgroundColor: '#ffffff',
        borderBottom: '1px solid #e2e8f0',
        padding: '1rem 2rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div
          style={{
            backgroundColor: '#0284c7',
            color: '#ffffff',
            padding: '0.5rem',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Shield size={22} />
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', margin: 0, lineHeight: 1.2, letterSpacing: '-0.02em' }}>
            ActuCore
          </h1>
          <p style={{ fontSize: '0.78rem', color: '#64748b', margin: 0 }}>
            Programmable ACTUS Contract Reconciliation on MST Blockchain
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            fontSize: '0.82rem',
            fontWeight: 500,
            backgroundColor: '#ecfdf5',
            color: '#047857',
            padding: '0.35rem 0.75rem',
            borderRadius: '20px',
            border: '1px solid #a7f3d0',
          }}
        >
          <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#10b981' }}></span>
          Backend API Ready (localhost:8000)
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            fontSize: '0.82rem',
            fontWeight: 500,
            backgroundColor: '#f1f5f9',
            color: '#475569',
            padding: '0.35rem 0.75rem',
            borderRadius: '20px',
            border: '1px solid #cbd5e1',
          }}
        >
          <Server size={14} />
          MST Testnet (91562037)
        </div>
      </div>
    </header>
  );
};
