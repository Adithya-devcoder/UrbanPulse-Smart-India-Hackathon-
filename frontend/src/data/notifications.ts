import type { Notification } from '../types';

export const mockNotifications: Notification[] = [
  {
    id: 'notif-1',
    type: 'hit-and-run',
    title: 'Possible Hit-and-Run Detected',
    location: 'Anna Salai',
    timestamp: new Date(Date.now() - 2 * 60 * 1000),
    read: false,
    incidentId: 'INC-2048',
  },
  {
    id: 'notif-2',
    type: 'pothole',
    title: 'High-Risk Pothole Detected',
    location: 'OMR',
    timestamp: new Date(Date.now() - 8 * 60 * 1000),
    read: false,
    incidentId: 'INC-2047',
  },
  {
    id: 'notif-3',
    type: 'waterlogging',
    title: 'Waterlogging Detected',
    location: 'Velachery',
    timestamp: new Date(Date.now() - 14 * 60 * 1000),
    read: false,
    incidentId: 'INC-2046',
  },
  {
    id: 'notif-4',
    type: 'resolved',
    title: 'Incident INC-2043 Resolved',
    timestamp: new Date(Date.now() - 20 * 60 * 1000),
    read: true,
    incidentId: 'INC-2043',
  },
  {
    id: 'notif-5',
    type: 'traffic',
    title: 'Traffic Congestion Worsening',
    location: 'GST Road',
    timestamp: new Date(Date.now() - 25 * 60 * 1000),
    read: true,
    incidentId: 'INC-2045',
  },
];
