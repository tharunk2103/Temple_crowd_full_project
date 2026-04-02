import React, { useState, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import AdminSidebar from './AdminSidebar';

import { 
  ExternalLink, 
  LayoutDashboard, 
  Users, 
  Map, 
  TrendingUp, 
  Gauge,
  ArrowRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';

const STREAMLIT_URL = 'http://localhost:8501';

const dashboardSections = [
  {
    id: 'dashboard',
    title: 'Dashboard',
    description: 'Overview of crowd management system',
    icon: LayoutDashboard,
    page: 'dashboard',
  },
  {
    id: 'monitoring',
    title: 'Crowd Monitoring',
    description: 'Real-time crowd density and flow analysis',
    icon: Users,
    page: 'monitoring',
  },
  {
    id: 'heatmap',
    title: 'Heatmap Analysis',
    description: 'Visual representation of crowd distribution',
    icon: Map,
    page: 'heatmap',
  },
  {
    id: 'analytics',
    title: 'Analytics & Trends',
    description: 'Historical data and predictive insights',
    icon: TrendingUp,
    page: 'analytics',
  },
  {
    id: 'threshold',
    title: 'Threshold Settings',
    description: 'Configure capacity limits and alerts',
    icon: Gauge,
    page: 'threshold',
  },
];

const AdminDashboard: React.FC = () => {
  const [activeItem, setActiveItem] = useState('dashboard');

  const { toast } = useToast();
const [lastAlertStatus, setLastAlertStatus] = useState<string>('');

useEffect(() => {
  const interval = setInterval(async () => {
    try {
      const res = await fetch('http://localhost:5001/status');
      const data = await res.json();

      if (data.status === 'OVERCROWDED' && lastAlertStatus !== 'OVERCROWDED') {
        toast({
          title: '🚨 OVERCROWDING ALERT!',
          description: `Total crowd: ${data.total_crowd} people. Take action immediately!`,
          variant: 'destructive',
        });
        setLastAlertStatus('OVERCROWDED');
      } else if (data.status === 'WARNING' && lastAlertStatus !== 'WARNING') {
        toast({
          title: '⚠️ Crowd Warning',
          description: `Crowd reaching ${data.total_crowd} people.`,
        });
        setLastAlertStatus('WARNING');
      } else if (data.status === 'NORMAL') {
        setLastAlertStatus('NORMAL');
      }

      if (data.audio_alert) {
        toast({
          title: '🎙️ PANIC DETECTED!',
          description: 'Loud noise detected! Check cameras immediately.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  }, 3000);

  return () => clearInterval(interval);
}, [lastAlertStatus]);

  const handleItemClick = (id: string) => {
    const section = dashboardSections.find(s => s.id === id);
    if (section) {
      // Open Streamlit in a new tab with page query parameter
      window.open(`${STREAMLIT_URL}/?page=${section.page}`, '_blank');
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <AdminSidebar activeItem={activeItem} onItemClick={handleItemClick} />
      
      {/* Main Content Area */}
      <main className="flex-1 p-8">
        {activeItem === 'dashboard' ? (
          <div className="max-w-4xl">
            {/* Welcome Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-foreground">Admin Control Panel</h1>
              <p className="text-muted-foreground mt-2">
                Select a section to view detailed analytics and reports.
              </p>
            </div>

            {/* Quick Access Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dashboardSections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => handleItemClick(section.id)}
                  className="card-elevated p-6 text-left hover:border-primary/50 transition-colors group"
                >
                  <div className="flex items-start justify-between">
                    <div className="p-3 rounded-lg bg-muted">
                      <section.icon className="w-6 h-6 text-primary" />
                    </div>
                    <ArrowRight className="w-5 h-5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mt-4">
                    {section.title}
                  </h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    {section.description}
                  </p>
                </button>
              ))}
            </div>

            {/* Info Banner */}
            <div className="card-elevated p-6 mt-8 bg-primary/5 border-primary/20">
              <div className="flex items-start gap-4">
                <div className="p-2 rounded-lg bg-primary/10">
                  <ExternalLink className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h4 className="font-medium text-foreground">External Analytics</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    Clicking on any section will open the corresponding Streamlit dashboard in a new tab for detailed analytics and visualizations.
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Placeholder for selected section */
          <div className="max-w-2xl">
            <div className="card-elevated p-8 text-center">
              <div className="p-4 rounded-full bg-muted inline-flex mb-4">
                <ExternalLink className="w-8 h-8 text-muted-foreground" />
              </div>
              <h2 className="text-xl font-semibold text-foreground">
                {dashboardSections.find(s => s.id === activeItem)?.title || 'Dashboard'}
              </h2>
              <p className="text-muted-foreground mt-2 mb-6">
                This section opens the external Streamlit dashboard in a new tab.
              </p>
              <Button variant="outline" onClick={() => setActiveItem('dashboard')}>
                <LayoutDashboard className="w-4 h-4 mr-2" />
                Back to Dashboard
              </Button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminDashboard;
