import { NavLink, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  LayoutDashboard, Map, Flame, AlertTriangle, Brain,
  TrendingUp, BarChart2, CheckSquare, FileText,
  Settings, User, Radio
} from 'lucide-react';

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    title: 'Overview',
    items: [
      { to: '/', icon: <LayoutDashboard size={16} />, label: 'Dashboard' },
    ],
  },
  {
    title: 'Intelligence',
    items: [
      { to: '/map', icon: <Map size={16} />, label: 'Live City Map' },
      { to: '/heatmap', icon: <Flame size={16} />, label: 'Risk Heatmap' },
      { to: '/incidents', icon: <AlertTriangle size={16} />, label: 'Incidents & Alerts' },
      { to: '/evidence', icon: <Brain size={16} />, label: 'AI Evidence' },
    ],
  },
  {
    title: 'Analytics',
    items: [
      { to: '/road-risk', icon: <TrendingUp size={16} />, label: 'Road Risk' },
      { to: '/reports', icon: <BarChart2 size={16} />, label: 'Traffic & Infrastructure' },
    ],
  },
  {
    title: 'Operations',
    items: [
      { to: '/actions', icon: <CheckSquare size={16} />, label: 'Action Center' },
      { to: '/reports-full', icon: <FileText size={16} />, label: 'Reports' },
    ],
  },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="flex flex-col w-60 min-h-screen bg-bg-secondary border-r border-border flex-shrink-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-border">
        <div className="flex items-center gap-3">
          {/* Geometric logo */}
          <div className="relative w-9 h-9 flex-shrink-0">
            <svg viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-9 h-9">
              {/* Road base */}
              <rect x="15" y="4" width="6" height="28" rx="2" fill="#3A2419" />
              <rect x="16.5" y="4" width="3" height="28" rx="1" fill="#D47A45" opacity="0.6" />
              {/* Location pin */}
              <circle cx="18" cy="14" r="5" fill="#D47A45" opacity="0.9" />
              <circle cx="18" cy="14" r="2.5" fill="#171717" />
              {/* Data nodes */}
              <circle cx="8" cy="10" r="2" fill="#E08A5A" opacity="0.7" />
              <circle cx="28" cy="10" r="2" fill="#E08A5A" opacity="0.7" />
              <circle cx="8" cy="26" r="2" fill="#D47A45" opacity="0.5" />
              <circle cx="28" cy="26" r="2" fill="#D47A45" opacity="0.5" />
              {/* Network lines */}
              <line x1="10" y1="10" x2="15" y2="12" stroke="#D47A45" strokeWidth="0.8" opacity="0.5" />
              <line x1="26" y1="10" x2="21" y2="12" stroke="#D47A45" strokeWidth="0.8" opacity="0.5" />
            </svg>
          </div>
          <div>
            <div className="text-text-primary font-semibold text-[15px] leading-tight tracking-tight">
              UrbanPulse
            </div>
            <div className="text-text-muted text-[10px] leading-tight mt-0.5">
              AI Urban Road Intelligence
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
        {navGroups.map((group) => (
          <div key={group.title}>
            <div className="text-text-muted text-[10px] font-semibold uppercase tracking-widest px-2 mb-2">
              {group.title}
            </div>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const isActive =
                  item.to === '/'
                    ? location.pathname === '/'
                    : location.pathname.startsWith(item.to);
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={clsx(
                      'flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all duration-200',
                      isActive
                        ? 'bg-cyan-muted text-cyan-primary shadow-cyan-glow font-medium'
                        : 'text-text-secondary hover:text-text-primary hover:bg-bg-elevated'
                    )}
                  >
                    <span className={clsx('flex-shrink-0', isActive ? 'text-cyan-primary' : 'text-text-muted')}>
                      {item.icon}
                    </span>
                    {item.label}
                    {isActive && (
                      <span className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan-primary animate-pulse-slow" />
                    )}
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Bottom */}
      <div className="px-3 py-4 border-t border-border space-y-0.5">
        <NavLink
          to="/settings"
          className={clsx(
            'flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all',
            location.pathname === '/settings'
              ? 'bg-cyan-muted text-cyan-primary'
              : 'text-text-secondary hover:text-text-primary hover:bg-bg-elevated'
          )}
        >
          <Settings size={16} className="text-text-muted" />
          Settings
        </NavLink>
        <div className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-text-secondary hover:bg-bg-elevated cursor-pointer transition-all">
          <div className="w-6 h-6 rounded-full bg-cyan-muted flex items-center justify-center flex-shrink-0">
            <User size={13} className="text-cyan-primary" />
          </div>
          <div className="min-w-0">
            <div className="text-text-primary text-xs font-medium truncate">Admin</div>
            <div className="text-text-muted text-[10px] truncate">Urban Operations</div>
          </div>
        </div>
        {/* Simulation indicator */}
        <div className="flex items-center gap-2 px-3 py-2">
          <Radio size={12} className="text-text-muted" />
          <span className="text-text-muted text-[10px]">v1.0.0 · Prototype</span>
        </div>
      </div>
    </aside>
  );
}
