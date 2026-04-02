import React from 'react';
import { AlertTriangle, CheckCircle, XCircle, Bell } from 'lucide-react';
import { CrowdStatus } from '@/types/auth';

interface StatusIndicatorProps {
  status: CrowdStatus;
  lastUpdated?: Date;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, lastUpdated = new Date() }) => {
  const statusConfig = {
    normal: {
      label: 'NORMAL',
      description: 'Crowd levels are within safe limits',
      className: 'status-safe',
      Icon: CheckCircle,
      animationClass: '',
    },
    warning: {
      label: 'WARNING',
      description: 'Approaching maximum capacity',
      className: 'status-warning',
      Icon: AlertTriangle,
      animationClass: 'warning-pulse',
    },
    overcrowded: {
      label: 'OVERCROWDED',
      description: 'Immediate action required',
      className: 'status-danger',
      Icon: XCircle,
      animationClass: 'alert-pulse alert-glow',
    },
  };

  const config = statusConfig[status];
  const { Icon, label, description, className, animationClass } = config;

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className={`rounded-xl p-6 ${className} ${animationClass} transition-all duration-300`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-full bg-white/20">
            <Icon className="w-8 h-8" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium opacity-80">STATUS:</span>
              <span className="text-xl font-bold">{label}</span>
            </div>
            <p className="text-sm opacity-80 mt-1">{description}</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {status === 'overcrowded' && (
            <div className="flex items-center gap-2 bg-white/20 rounded-lg px-3 py-2 animate-pulse">
              <Bell className="w-5 h-5" />
              <span className="text-sm font-semibold">ALERT ACTIVE</span>
            </div>
          )}
          <div className="text-right opacity-80">
            <p className="text-xs">Updated</p>
            <p className="text-sm font-medium">{formatTime(lastUpdated)}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatusIndicator;
