// UrbanPulse Type Definitions
// These interfaces define the shape of data that will be returned by real APIs later

export type IncidentType = 'accident' | 'pothole' | 'waterlogging' | 'traffic' | 'infrastructure' | 'hit-and-run' | 'road-hazard';
export type SeverityLevel = 'critical' | 'high' | 'medium' | 'low';
export type IncidentStatus = 'new' | 'under-review' | 'verified' | 'assigned' | 'in-progress' | 'resolved' | 'rejected';
export type ActionStatus = 'new' | 'verified' | 'assigned' | 'in-progress' | 'resolved' | 'rejected';
export type CameraStatus = 'online' | 'offline' | 'degraded';
export type MapLayer = 'incidents' | 'potholes' | 'waterlogging' | 'traffic' | 'roadRisk' | 'cameras' | 'closures';

export interface Coordinates {
  lat: number;
  lng: number;
  // For SVG map: normalized 0-1 values mapped to canvas
  x: number;
  y: number;
}

export interface Incident {
  id: string;
  type: IncidentType;
  title: string;
  location: string;
  severity: SeverityLevel;
  status: IncidentStatus;
  aiConfidence: number;
  detectedAt: Date;
  coordinates: Coordinates;
  cameraId?: string;
  vehicleIds?: string[];
  description: string;
  evidenceFrames: number;
  timelineEvents: TimelineEvent[];
  aiAssessment: string;
  responseTeam?: string;
  eta?: string;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  label: string;
  icon: string;
  vehicleRef?: 'A' | 'B';
  observation: string;
  frameIndex: number;
}

export interface Vehicle {
  id: string;
  trackingId: string;
  type: string;
  color: string;
  numberPlate?: string;
  plateConfidence?: number;
  direction?: string;
  lane?: string;
  coordinates: Coordinates;
}

export interface Camera {
  id: string;
  location: string;
  status: CameraStatus;
  lastFrame: string;
  coordinates: Coordinates;
  coverageRadius: number;
}

export interface Road {
  id: string;
  name: string;
  riskScore: number;
  trend: number; // percentage change
  accidentCount: number;
  potholeCount: number;
  waterloggingCount: number;
  trafficIncidents: number;
  avgResponseTime: number; // minutes
  length: number; // km
  aiRecommendation: string;
  historicalData: { date: string; score: number }[];
  coordinates: { start: Coordinates; end: Coordinates };
}

export interface HeatmapZone {
  id: string;
  name: string;
  riskScore: number;
  intensity: 'low' | 'medium' | 'high' | 'critical';
  incidentCount: number;
  potholeCount: number;
  waterloggingCount: number;
  avgResponseTime: number;
  trend: number;
  coordinates: Coordinates;
  radius: number; // SVG radius
}

export interface Notification {
  id: string;
  type: IncidentType | 'system' | 'resolved';
  title: string;
  location?: string;
  timestamp: Date;
  read: boolean;
  incidentId?: string;
}

export interface AnalyticsData {
  incidentTrends: { date: string; accidents: number; potholes: number; waterlogging: number; traffic: number }[];
  distribution: { name: string; value: number; color: string }[];
  responsePerformance: {
    avgResponseTime: number;
    resolutionRate: number;
    criticalResponseTime: number;
  };
  aiPerformance: {
    detectionAccuracy: number;
    falsePositiveRate: number;
    avgConfidence: number;
    totalDetections: number;
  };
}

export interface Action {
  id: string;
  incidentId: string;
  incidentType: IncidentType;
  title: string;
  location: string;
  severity: SeverityLevel;
  status: ActionStatus;
  assignedTo: string;
  priority: 'immediate' | 'high' | 'medium' | 'low';
  eta?: string;
  notes?: string;
  createdAt: Date;
}

export interface RiskSummary {
  overall: number;
  status: string;
  accidentRisk: number;
  roadCondition: number;
  trafficRisk: number;
  waterloggingRisk: number;
  infrastructureRisk: number;
}
