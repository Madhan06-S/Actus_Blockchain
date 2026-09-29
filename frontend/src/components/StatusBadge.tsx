import React from 'react';
import type { FinancialStatus } from '../types/contract';
import { AlertTriangle, CheckCircle2, Clock, AlertOctagon } from 'lucide-react';

interface StatusBadgeProps {
  status: FinancialStatus;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'DEVIATION_DETECTED':
        return {
          label: 'DEVIATION DETECTED',
          bg: 'var(--danger-bg)',
          color: 'var(--danger)',
          border: 'var(--danger-border)',
          icon: AlertOctagon,
        };
      case 'ON_TRACK':
        return {
          label: 'ON TRACK',
          bg: 'var(--success-bg)',
          color: 'var(--success)',
          border: 'var(--success-border)',
          icon: CheckCircle2,
        };
      case 'OVERDUE':
        return {
          label: 'OVERDUE PAYMENTS',
          bg: 'var(--warning-bg)',
          color: 'var(--warning)',
          border: 'var(--warning-border)',
          icon: Clock,
        };
      case 'COMPLETED':
        return {
          label: 'FULLY COMPLETED',
          bg: 'var(--success-bg)',
          color: 'var(--success)',
          border: 'var(--success-border)',
          icon: CheckCircle2,
        };
      default:
        return {
          label: 'UNKNOWN',
          bg: '#f1f5f9',
          color: 'var(--text-muted)',
          border: '#e2e8f0',
          icon: AlertTriangle,
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  const sizeClasses = {
    sm: { padding: '0.25rem 0.6rem', fontSize: '0.75rem', iconSize: 14 },
    md: { padding: '0.4rem 0.85rem', fontSize: '0.85rem', iconSize: 16 },
    lg: { padding: '0.6rem 1.2rem', fontSize: '1rem', iconSize: 20 },
  }[size];

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.4rem',
        backgroundColor: config.bg,
        color: config.color,
        border: `1px solid ${config.border}`,
        borderRadius: '20px',
        fontWeight: 700,
        letterSpacing: '0.04em',
        padding: sizeClasses.padding,
        fontSize: sizeClasses.fontSize,
      }}
    >
      <Icon size={sizeClasses.iconSize} />
      {config.label}
    </span>
  );
};
