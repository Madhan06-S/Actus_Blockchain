import React from 'react';
import { LayoutDashboard, FileText, Calendar, Activity, CheckSquare } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'contract', label: 'Contract Details', icon: FileText },
    { id: 'schedule', label: 'Expected Schedule', icon: Calendar },
    { id: 'activity', label: 'Recorded Activity', icon: Activity },
    { id: 'integrity', label: 'Integrity Verification', icon: CheckSquare },
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
        Navigation
      </div>
      {navItems.map((item) => {
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
              padding: '0.7rem 0.85rem',
              borderRadius: '8px',
              fontSize: '0.9rem',
              fontWeight: isActive ? 600 : 500,
              color: isActive ? '#0284c7' : '#475569',
              backgroundColor: isActive ? '#f0f9ff' : 'transparent',
              borderLeft: isActive ? '3px solid #0284c7' : '3px solid transparent',
              textAlign: 'left',
              width: '100%',
            }}
          >
            <Icon size={18} color={isActive ? '#0284c7' : '#64748b'} />
            {item.label}
          </button>
        );
      })}
    </aside>
  );
};
