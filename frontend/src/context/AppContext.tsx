import React, { createContext, useContext, useState, useCallback } from 'react';
import type { Incident, Notification } from '../types';
import { mockIncidents } from '../data/incidents';
import { mockNotifications } from '../data/notifications';

interface Toast {
  id: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'critical';
}

interface AppContextType {
  // Active incident for cross-page navigation
  activeIncidentId: string | null;
  setActiveIncidentId: (id: string | null) => void;

  // Incidents state (can grow via simulation)
  incidents: Incident[];
  setIncidents: React.Dispatch<React.SetStateAction<Incident[]>>;

  // Notifications
  notifications: Notification[];
  setNotifications: React.Dispatch<React.SetStateAction<Notification[]>>;
  unreadCount: number;
  markAllRead: () => void;

  // Live simulation
  simulationEnabled: boolean;
  toggleSimulation: () => void;

  // Map layers
  mapLayers: Record<string, boolean>;
  toggleLayer: (layer: string) => void;

  // Search
  searchQuery: string;
  setSearchQuery: (q: string) => void;

  // Toast notifications
  toasts: Toast[];
  addToast: (message: string, type?: Toast['type']) => void;
  removeToast: (id: string) => void;

  // Navigation helper
  navigateTo: string | null;
  setNavigateTo: (path: string | null) => void;
}

const AppContext = createContext<AppContextType | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [activeIncidentId, setActiveIncidentId] = useState<string | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>(mockIncidents);
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications);
  const [simulationEnabled, setSimulationEnabled] = useState(true);
  const [mapLayers, setMapLayers] = useState<Record<string, boolean>>({
    incidents: true,
    potholes: true,
    waterlogging: true,
    traffic: true,
    roadRisk: true,
    cameras: true,
    closures: false,
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [navigateTo, setNavigateTo] = useState<string | null>(null);

  const toggleSimulation = useCallback(() => setSimulationEnabled((p) => !p), []);

  const toggleLayer = useCallback((layer: string) => {
    setMapLayers((prev) => ({ ...prev, [layer]: !prev[layer] }));
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const addToast = useCallback((message: string, type: Toast['type'] = 'info') => {
    const id = `toast-${Date.now()}`;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <AppContext.Provider
      value={{
        activeIncidentId,
        setActiveIncidentId,
        incidents,
        setIncidents,
        notifications,
        setNotifications,
        unreadCount,
        markAllRead,
        simulationEnabled,
        toggleSimulation,
        mapLayers,
        toggleLayer,
        searchQuery,
        setSearchQuery,
        toasts,
        addToast,
        removeToast,
        navigateTo,
        setNavigateTo,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
