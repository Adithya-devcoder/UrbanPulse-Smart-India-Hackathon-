import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, ChevronDown, User, Power } from 'lucide-react';
import { clsx } from 'clsx';
import { useApp } from '../../context/AppContext';
import { formatDistanceToNow } from 'date-fns';

interface HeaderProps {
  title: string;
  subtitle: string;
}

const notifTypeConfig = {
  'hit-and-run': { dot: 'bg-coral-critical', icon: '🔴' },
  accident: { dot: 'bg-coral-critical', icon: '🔴' },
  pothole: { dot: 'bg-amber-warning', icon: '🟠' },
  waterlogging: { dot: 'bg-cyan-primary', icon: '💧' },
  traffic: { dot: 'bg-amber-warning', icon: '🟡' },
  infrastructure: { dot: 'bg-success', icon: '🔧' },
  'road-hazard': { dot: 'bg-amber-warning', icon: '🟠' },
  resolved: { dot: 'bg-success', icon: '✓' },
  system: { dot: 'bg-cyan-primary', icon: '⚙' },
};

export default function Header({ title, subtitle }: HeaderProps) {
  const navigate = useNavigate();
  const { notifications, unreadCount, markAllRead, setActiveIncidentId, simulationEnabled, toggleSimulation, searchQuery, setSearchQuery } = useApp();
  const [showNotifs, setShowNotifs] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifs(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  useEffect(() => {
    if (showSearch) searchRef.current?.focus();
  }, [showSearch]);

  function handleNotifClick(incidentId?: string) {
    setShowNotifs(false);
    if (incidentId) {
      setActiveIncidentId(incidentId);
      navigate('/evidence');
    }
  }

  function handleSearch(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && searchQuery.trim()) {
      const q = searchQuery.trim().toUpperCase();
      if (q.startsWith('INC-')) {
        setActiveIncidentId(q);
        navigate('/evidence');
      } else if (q.startsWith('CAM-')) {
        navigate('/map');
      } else {
        navigate('/incidents');
      }
      setShowSearch(false);
    }
    if (e.key === 'Escape') {
      setShowSearch(false);
      setSearchQuery('');
    }
  }

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-bg-secondary flex-shrink-0">
      {/* Left: Title */}
      <div>
        <h1 className="text-text-primary font-semibold text-lg leading-tight">{title}</h1>
        <p className="text-text-muted text-xs mt-0.5">{subtitle}</p>
      </div>

      {/* Right: Controls */}
      <div className="flex items-center gap-3">
        {/* Simulation Toggle */}
        <button
          onClick={toggleSimulation}
          className={clsx(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border',
            simulationEnabled
              ? 'border-cyan-primary/30 bg-cyan-muted text-cyan-primary'
              : 'border-border text-text-muted hover:text-text-secondary'
          )}
          title="Toggle live simulation"
        >
          <Power size={11} />
          Live {simulationEnabled ? 'ON' : 'OFF'}
        </button>

        {/* Search */}
        <div className="relative">
          {showSearch ? (
            <input
              ref={searchRef}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearch}
              placeholder="Search INC-2048, road, camera…"
              className="w-64 px-3 py-1.5 bg-bg-elevated border border-cyan-primary/40 rounded-lg text-text-primary text-sm placeholder:text-text-muted focus:outline-none focus:border-cyan-primary transition-all"
            />
          ) : (
            <button
              onClick={() => setShowSearch(true)}
              className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-elevated transition-all"
              title="Search"
            >
              <Search size={18} />
            </button>
          )}
        </div>

        {/* Notifications */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => { setShowNotifs((p) => !p); if (!showNotifs) markAllRead(); }}
            className="relative p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-elevated transition-all"
            title="Notifications"
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-coral-critical text-white text-[9px] font-bold flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </button>

          {showNotifs && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-bg-elevated border border-border rounded-2xl shadow-elevated z-50 animate-slide-in overflow-hidden">
              <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                <span className="text-text-primary text-sm font-medium">Notifications</span>
                <span className="text-text-muted text-xs">{notifications.length} total</span>
              </div>
              <div className="max-h-80 overflow-y-auto">
                {notifications.slice(0, 8).map((n) => {
                  const cfg = notifTypeConfig[n.type] || notifTypeConfig.system;
                  return (
                    <button
                      key={n.id}
                      onClick={() => handleNotifClick(n.incidentId)}
                      className="w-full flex items-start gap-3 px-4 py-3 hover:bg-bg-secondary text-left transition-all border-b border-border/50 last:border-b-0"
                    >
                      <span className="text-sm flex-shrink-0 mt-0.5">{cfg.icon}</span>
                      <div className="min-w-0 flex-1">
                        <div className="text-text-primary text-xs font-medium leading-tight">{n.title}</div>
                        {n.location && <div className="text-text-muted text-[10px] mt-0.5">{n.location}</div>}
                        <div className="text-text-muted text-[10px] mt-0.5">
                          {formatDistanceToNow(n.timestamp, { addSuffix: true })}
                        </div>
                      </div>
                      {!n.read && <span className={clsx('w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5', cfg.dot)} />}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* System Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg-elevated border border-border">
          <span className="relative flex w-2 h-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-success" />
          </span>
          <span className="text-text-secondary text-xs">All Systems Operational</span>
        </div>

        {/* Admin */}
        <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-bg-elevated transition-all border border-transparent hover:border-border">
          <div className="w-7 h-7 rounded-full bg-cyan-muted flex items-center justify-center">
            <User size={14} className="text-cyan-primary" />
          </div>
          <div className="text-left hidden sm:block">
            <div className="text-text-primary text-xs font-medium leading-tight">Admin</div>
            <div className="text-text-muted text-[10px] leading-tight">Urban Operations</div>
          </div>
          <ChevronDown size={13} className="text-text-muted" />
        </button>
      </div>
    </header>
  );
}
