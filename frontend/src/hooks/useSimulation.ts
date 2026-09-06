import { useEffect, useRef } from 'react';
import { useApp } from '../context/AppContext';
import type { Notification } from '../types';

const simulatedNewIncidents = [
  { msg: 'Pothole detected on Rajiv Gandhi Salai', type: 'info' as const },
  { msg: 'Waterlogging alert on Poonamallee High Road', type: 'warning' as const },
  { msg: 'Traffic congestion building on ECR', type: 'warning' as const },
  { msg: 'New AI detection: road hazard on Sardar Patel Road', type: 'info' as const },
];

let simIndex = 0;

export function useSimulation() {
  const { simulationEnabled, addToast, setNotifications } = useApp();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!simulationEnabled) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }

    // Run every 15 seconds
    intervalRef.current = setInterval(() => {
      const item = simulatedNewIncidents[simIndex % simulatedNewIncidents.length];
      simIndex++;

      // Add toast
      addToast(item.msg, item.type);

      // Add notification
      const newNotif: Notification = {
        id: `sim-notif-${Date.now()}`,
        type: simIndex % 2 === 0 ? 'pothole' : 'traffic',
        title: item.msg,
        timestamp: new Date(),
        read: false,
      };

      setNotifications((prev) => [newNotif, ...prev.slice(0, 19)]);
    }, 15000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [simulationEnabled, addToast, setNotifications]);
}
