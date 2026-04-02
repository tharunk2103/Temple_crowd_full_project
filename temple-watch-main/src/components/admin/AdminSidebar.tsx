import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { 
  LayoutDashboard, 
  Users, 
  Map, 
  TrendingUp, 
  Gauge, 
  LogOut,
  Building2,
  ChevronRight
} from 'lucide-react';

interface SidebarItem {
  id: string;
  label: string;
  icon: React.ElementType;
  href?: string;
}

const sidebarItems: SidebarItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'monitoring', label: 'Crowd Monitoring', icon: Users },
  { id: 'heatmap', label: 'Heatmap', icon: Map },
  { id: 'analytics', label: 'Analytics & Trends', icon: TrendingUp },
  { id: 'threshold', label: 'Threshold Count', icon: Gauge },
];

interface AdminSidebarProps {
  activeItem: string;
  onItemClick: (id: string) => void;
}

const AdminSidebar: React.FC<AdminSidebarProps> = ({ activeItem, onItemClick }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <aside className="w-64 min-h-screen sidebar-nav flex flex-col">
      {/* Logo/Header */}
      <div className="p-6 border-b border-sidebar-border">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-sidebar-primary">
            <Building2 className="w-5 h-5 text-sidebar-primary-foreground" />
          </div>
          <div>
            <h1 className="font-semibold text-sidebar-foreground">Temple CMS</h1>
            <p className="text-xs text-sidebar-foreground/60">Admin Panel</p>
          </div>
        </div>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 p-4 space-y-1">
        {sidebarItems.map((item) => {
          const isActive = activeItem === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onItemClick(item.id)}
              className={`sidebar-item w-full group ${isActive ? 'active' : ''}`}
            >
              <item.icon className={`w-5 h-5 transition-colors ${isActive ? 'text-sidebar-primary-foreground' : 'text-sidebar-foreground/70 group-hover:text-sidebar-foreground'}`} />
              <span className={`text-sm font-medium flex-1 text-left ${isActive ? '' : 'text-sidebar-foreground/70 group-hover:text-sidebar-foreground'}`}>
                {item.label}
              </span>
              {isActive && (
                <ChevronRight className="w-4 h-4 text-sidebar-primary-foreground/70" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Role Badge & Logout */}
      <div className="p-4 border-t border-sidebar-border space-y-3">
        <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-sidebar-accent/50">
          <div className="w-2 h-2 rounded-full bg-[hsl(var(--status-safe))]" />
          <span className="text-xs text-sidebar-foreground/70">Role:</span>
          <span className="text-xs font-semibold text-sidebar-foreground">Administrator</span>
        </div>
        <button
          onClick={handleLogout}
          className="sidebar-item w-full text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-[hsl(var(--status-danger)/0.1)]"
        >
          <LogOut className="w-5 h-5" />
          <span className="text-sm font-medium">Logout</span>
        </button>
      </div>
    </aside>
  );
};

export default AdminSidebar;
