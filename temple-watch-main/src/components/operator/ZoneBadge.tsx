import React from 'react';
import { CrowdStatus } from '@/types/auth';

interface ZoneBadgeProps {
  status: CrowdStatus;
  showLabel?: boolean;
}

const ZoneBadge: React.FC<ZoneBadgeProps> = ({ status, showLabel = true }) => {
  const statusConfig = {
    normal: {
      label: 'Normal',
      className: 'badge-safe',
    },
    warning: {
      label: 'Warning',
      className: 'badge-warning',
    },
    overcrowded: {
      label: 'Critical',
      className: 'badge-danger',
    },
  };

  const config = statusConfig[status];

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold ${config.className}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${status === 'overcrowded' ? 'bg-[hsl(var(--status-danger))] pulse-indicator' : status === 'warning' ? 'bg-[hsl(var(--status-warning))]' : 'bg-[hsl(var(--status-safe))]'}`} />
      {showLabel && config.label}
    </span>
  );
};

export default ZoneBadge;
