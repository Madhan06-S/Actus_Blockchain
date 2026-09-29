import React from 'react';
import { LayoutDashboard, FileText, Calendar, Activity, CheckSquare, ShieldAlert, TrendingUp, Handshake, Landmark } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const coreNavItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'contract', label: 'Contract Details', icon: FileText },
    { id: 'schedule', label: 'Expected Schedule', icon: Calendar },
    { id: 'activity', label: 'Recorded Activity', icon: Activity },
    { id: 'integrity', label: 'Integrity Verification', icon: CheckSquare },
  ];

  const intelligenceNavItems = [
    { id: 'risk', label: 'AI Risk Analysis', icon: ShieldAlert },
    { id: 'stress', label: 'Stress Testing', icon: TrendingUp },
    { id: 'negotiation', label: 'Negotiation Assistant', icon: Handshake },
    { id: 'liquidity', label: 'Portfolio Liquidity', icon: Landmark },
  ];

  return (
    <aside
      style={{
        width: '240px',
        backgroundColor: '#ffffff',
        borderRight: '1px solid #e2e8f0',
        padding: '1.5rem 1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
        minHeight: 'calc(100vh - 65px)',
      }}
    >
      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', padding: '0 0.75rem 0.5rem 0.75rem', letterSpacing: '0.05em' }}>
        Core Contract
      </div>
      {coreNavItems.map((item) => {
        const Icon = item.icon;
        const isActive = activeTab === item.id;
        return (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.65rem 0.85rem',
              borderRadius: '8px',
              fontSize: '0.88rem',
              fontWeight: isActive ? 600 : 500,
              color: isActive ? '#0284c7' : '#475569',
              backgroundColor: isActive ? '#f0f9ff' : 'transparent',
              borderLeft: isActive ? '3px solid #0284c7' : '3px solid transparent',
              textAlign: 'left',
              width: '100%',
              cursor: 'pointer',
            }}
          >
            <Icon size={17} color={isActive ? '#0284c7' : '#64748b'} />
            {item.label}
          </button>
        );
      })}

      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', padding: '1rem 0.75rem 0.5rem 0.75rem', letterSpacing: '0.05em' }}>
        Financial Intelligence
      </div>
      {intelligenceNavItems.map((item) => {
        const Icon = item.icon;
        const isActive = activeTab === item.id;
        return (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.65rem 0.85rem',
              borderRadius: '8px',
              fontSize: '0.88rem',
              fontWeight: isActive ? 600 : 500,
              color: isActive ? '#0284c7' : '#475569',
              backgroundColor: isActive ? '#f0f9ff' : 'transparent',
              borderLeft: isActive ? '3px solid #0284c7' : '3px solid transparent',
              textAlign: 'left',
              width: '100%',
              cursor: 'pointer',
            }}
          >
            <Icon size={17} color={isActive ? '#0284c7' : '#64748b'} />
            {item.label}
          </button>
        );
      })}
    </aside>
  );
};
