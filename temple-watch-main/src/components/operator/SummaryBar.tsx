import React from 'react';
import { Users, Activity, Clock, Shield } from 'lucide-react';
import { CrowdStatus } from '@/types/auth';

interface SummaryBarProps {
  totalCrowd: number;
  status: CrowdStatus;
  lastUpdated: Date;
  role: 'operator' | 'admin';
}

const SummaryBar: React.FC<SummaryBarProps> = ({ totalCrowd, status, lastUpdated, role }) => {
  const statusConfig = {
    normal: {
      label: 'Normal',
      badgeClass: 'badge-safe',
      dotClass: 'bg-[hsl(var(--status-safe))]',
    },
    warning: {
      label: 'Warning',
      badgeClass: 'badge-warning',
      dotClass: 'bg-[hsl(var(--status-warning))]',
    },
    overcrowded: {
      label: 'Overcrowded',
      badgeClass: 'badge-danger',
      dotClass: 'bg-[hsl(var(--status-danger))] alert-pulse',
    },
  };

  const config = statusConfig[status];

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className="bg-card border-b border-border">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between flex-wrap gap-4">
          {/* Left: Role Indicator */}
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-muted-foreground">Role:</span>
            <span className="text-sm font-semibold text-foreground capitalize">{role}</span>
          </div>

          {/* Center: Stats */}
          <div className="flex items-center gap-6">
            {/* Total Crowd */}
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-md bg-primary/10">
                <Users className="w-4 h-4 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total Crowd</p>
                <p className="text-lg font-bold text-foreground">{totalCrowd.toLocaleString()}</p>
              </div>
            </div>

            {/* System Status */}
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-md bg-primary/10">
                <Activity className="w-4 h-4 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">System Status</p>
                <div className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${config.dotClass}`} />
                  <span className={`text-sm font-semibold px-2 py-0.5 rounded-full ${config.badgeClass}`}>
                    {config.label}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Last Updated */}
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock className="w-4 h-4" />
            <div>
              <p className="text-xs">Last Updated</p>
              <p className="text-sm font-medium text-foreground">{formatTime(lastUpdated)}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SummaryBar;
