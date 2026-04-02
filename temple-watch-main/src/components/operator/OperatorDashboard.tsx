import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { LogOut, Radio, RefreshCw } from 'lucide-react';
import LiveFeedCard from './LiveFeedCard';
import CountCard from './CountCard';
import StatusIndicator from './StatusIndicator';
import SummaryBar from './SummaryBar';
import { CrowdStatus } from '@/types/auth';
import { useToast } from '@/hooks/use-toast';

const API_BASE = 'http://localhost:5001';

interface ZoneCounts {
  Entrance: number;
  Queue: number;
  Sanctum: number;
  Exit: number;
}

interface StatusResponse {
  status: 'NORMAL' | 'WARNING' | 'OVERCROWDED';
  total_crowd: number;
  threshold: number;
  zones: ZoneCounts;
  audio_alert: boolean;
}

const OperatorDashboard: React.FC = () => {
  const { logout } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [zoneCounts, setZoneCounts] = useState<ZoneCounts>({
    Entrance: 0,
    Queue: 0,
    Sanctum: 0,
    Exit: 0,
  });
  const [currentStatus, setCurrentStatus] = useState<CrowdStatus>('normal');
  const [loading, setLoading] = useState(true);
  const [lastAlertStatus, setLastAlertStatus] = useState<string>('');
  const [lastAudioAlert, setLastAudioAlert] = useState<boolean>(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleRefresh = () => {
    fetchLiveData();
    setLastUpdated(new Date());
  };

  const fetchLiveData = async () => {
    try {
      // Fetch live counts
      const countsResponse = await fetch(`${API_BASE}/live_counts`);
      if (countsResponse.ok) {
        const counts: ZoneCounts = await countsResponse.json();
        setZoneCounts(counts);
      }

      // Fetch status
      const statusResponse = await fetch(`${API_BASE}/status`);
      if (statusResponse.ok) {
        const statusData: StatusResponse = await statusResponse.json(); 
        const statusMap: Record<string, CrowdStatus> = {
          'NORMAL': 'normal',
          'WARNING': 'warning',
          'OVERCROWDED': 'overcrowded',
};
setCurrentStatus(statusMap[statusData.status] || 'normal');

// 🔔 Show toast alert when status changes to WARNING or OVERCROWDED
if (statusData.status === 'OVERCROWDED' && lastAlertStatus !== 'OVERCROWDED') {
  toast({
    title: '🚨 OVERCROWDING ALERT!',
    description: `Total crowd: ${statusData.total_crowd} people. Threshold exceeded!`,
    variant: 'destructive',
  });
  setLastAlertStatus('OVERCROWDED');
} else if (statusData.status === 'WARNING' && lastAlertStatus !== 'WARNING') {
  toast({
    title: '⚠️ Crowd Warning',
    description: `Crowd reaching ${statusData.total_crowd} people. Monitor closely.`,
  });
  setLastAlertStatus('WARNING');
} else if (statusData.status === 'NORMAL') {
  setLastAlertStatus('NORMAL');
}

// 🔔 Audio panic alert
if (statusData.audio_alert && !lastAudioAlert) {
  toast({
    title: '🎙️ PANIC DETECTED!',
    description: 'Loud noise/screaming detected! Check camera feeds immediately.',
    variant: 'destructive',
  });
}
setLastAudioAlert(statusData.audio_alert);
      }
    } catch (error) {
      console.error('Error fetching live data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Poll APIs every 1-2 seconds
  useEffect(() => {
    fetchLiveData();
    const interval = setInterval(() => {
      fetchLiveData();
      setLastUpdated(new Date());
    }, 1500); // Poll every 1.5 seconds
    return () => clearInterval(interval);
  }, []);

  // Auto-update timestamp every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdated(new Date());
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const totalCount = Object.values(zoneCounts).reduce((sum, count) => sum + count, 0);

  // Map zone counts to zone data format.
  // feedZone = backend API key (Entrance, Queue, Sanctum, Exit); name = display label.
  const zoneData = [
    { id: 'entrance', name: 'Entrance', feedZone: 'Entrance', count: zoneCounts.Entrance, status: 'normal' as CrowdStatus, trend: 'stable' as const },
    { id: 'queue', name: 'Queue Area', feedZone: 'Queue', count: zoneCounts.Queue, status: 'normal' as CrowdStatus, trend: 'stable' as const },
    { id: 'sanctum', name: 'Sanctum', feedZone: 'Sanctum', count: zoneCounts.Sanctum, status: 'normal' as CrowdStatus, trend: 'stable' as const },
    { id: 'exit', name: 'Exit', feedZone: 'Exit', count: zoneCounts.Exit, status: 'normal' as CrowdStatus, trend: 'stable' as const },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Summary Bar */}
      <SummaryBar 
        totalCrowd={totalCount} 
        status={currentStatus} 
        lastUpdated={lastUpdated}
        role="operator"
      />

      {/* Top Navigation Bar */}
      <header className="bg-card border-b border-border sticky top-0 z-10">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[hsl(var(--status-danger)/0.1)]">
              <Radio className="w-5 h-5 text-[hsl(var(--status-danger))]" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-foreground">Live Crowd Monitoring</h1>
              <p className="text-xs text-muted-foreground">Operator View</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Status Indicator - Prominent at top */}
        <section>
          <StatusIndicator status={currentStatus} lastUpdated={lastUpdated} />
        </section>

        {/* Current Count Section */}
        <section>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">
            Current Count by Zone
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {zoneData.map((zone) => (
              <CountCard 
                key={zone.id} 
                zone={zone.name} 
                count={zone.count} 
                status={zone.status}
                trend={zone.trend}
              />
            ))}
            <CountCard zone="Total Crowd" count={totalCount} isTotal />
          </div>
        </section>

        {/* Live Feeds Section */}
        <section>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">
            Live Camera Feeds
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {zoneData.map((zone) => (
              <LiveFeedCard 
                key={zone.id} 
                zone={zone.name}
                feedZone={zone.feedZone}
                status={zone.status}
                lastUpdated={lastUpdated}
              />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
};

export default OperatorDashboard;
