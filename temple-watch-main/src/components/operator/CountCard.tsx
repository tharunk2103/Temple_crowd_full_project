import React from 'react';
import { Users, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { CrowdStatus } from '@/types/auth';
import ZoneBadge from './ZoneBadge';

interface CountCardProps {
  zone: string;
  count: number;
  isTotal?: boolean;
  status?: CrowdStatus;
  trend?: 'up' | 'down' | 'stable';
}

const CountCard: React.FC<CountCardProps> = ({ 
  zone, 
  count, 
  isTotal = false, 
  status = 'normal',
  trend = 'stable'
}) => {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'text-[hsl(var(--status-danger))]' : trend === 'down' ? 'text-[hsl(var(--status-safe))]' : 'text-muted-foreground';

  const cardClass = isTotal 
    ? 'bg-primary text-primary-foreground' 
    : status === 'overcrowded' 
      ? 'alert-glow border-[hsl(var(--status-danger)/0.5)]' 
      : status === 'warning'
        ? 'warning-pulse border-[hsl(var(--status-warning)/0.3)]'
        : '';

  return (
    <div className={`card-elevated p-4 transition-all duration-300 ${cardClass}`}>
      <div className="flex items-start justify-between mb-2">
        <p className={`text-sm font-medium ${isTotal ? 'text-primary-foreground/80' : 'text-muted-foreground'}`}>
          {zone}
        </p>
        {!isTotal && <ZoneBadge status={status} />}
      </div>
      
      <div className="flex items-end justify-between">
        <div className="flex items-center gap-2">
          <p className={`text-3xl font-bold ${isTotal ? 'text-primary-foreground' : 'text-foreground'}`}>
            {count.toLocaleString()}
          </p>
          {!isTotal && (
            <TrendIcon className={`w-4 h-4 ${trendColor}`} />
          )}
        </div>
        <div className={`p-2.5 rounded-lg ${isTotal ? 'bg-primary-foreground/10' : 'bg-muted'}`}>
          <Users className={`w-5 h-5 ${isTotal ? 'text-primary-foreground' : 'text-muted-foreground'}`} />
        </div>
      </div>
    </div>
  );
};

export default CountCard;
