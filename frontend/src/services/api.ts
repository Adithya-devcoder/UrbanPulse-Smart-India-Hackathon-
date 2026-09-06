/**
 * UrbanPulse — Frontend API Service
 * Connects React frontend to FastAPI backend (port 8000).
 * Automatically falls back to mock data if backend is unreachable.
 */

import { mockIncidents, getIncidentById } from '../data/incidents';
import { mockRoads } from '../data/roads';
import { mockCameras } from '../data/cameras';
import { mockHeatmapZones } from '../data/heatmap';
import { mockNotifications } from '../data/notifications';
import { mockAnalytics, mockActions } from '../data/analytics';
import type {
  Incident, Road, Camera, HeatmapZone,
  Notification, AnalyticsData, Action
} from '../types';

// ── Config ────────────────────────────────────────────────────────────────────
const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1';
const TIMEOUT_MS = 4000;

// ── Base fetch with timeout + error handling ──────────────────────────────────
async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...(options?.headers ?? {}),
      },
    });
    clearTimeout(timer);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();
    // Backend wraps responses in { success, data, message }
    return (json?.data ?? json) as T;
  } catch (err) {
    clearTimeout(timer);
    throw err;
  }
}

// ── Incidents ─────────────────────────────────────────────────────────────────
export async function fetchIncidents(): Promise<Incident[]> {
  try {
    return await apiFetch<Incident[]>('/incidents');
  } catch {
    console.warn('[API] Backend unavailable — using mock incidents');
    return mockIncidents;
  }
}

export async function fetchIncidentById(id: string): Promise<Incident | undefined> {
  try {
    return await apiFetch<Incident>(`/incidents/${id}`);
  } catch {
    return getIncidentById(id);
  }
}

export async function updateIncidentStatus(id: string, status: string): Promise<void> {
  try {
    await apiFetch(`/incidents/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  } catch {
    console.warn(`[API] PATCH /incidents/${id} failed (offline mode)`);
  }
}

// ── Roads ─────────────────────────────────────────────────────────────────────
export async function fetchRoads(): Promise<Road[]> {
  try {
    return await apiFetch<Road[]>('/roads');
  } catch {
    return mockRoads;
  }
}

// ── Cameras ───────────────────────────────────────────────────────────────────
export async function fetchCameras(): Promise<Camera[]> {
  try {
    return await apiFetch<Camera[]>('/cameras');
  } catch {
    return mockCameras;
  }
}

// ── Heatmap ───────────────────────────────────────────────────────────────────
export async function fetchHeatmapZones(): Promise<HeatmapZone[]> {
  try {
    return await apiFetch<HeatmapZone[]>('/heatmap');
  } catch {
    return mockHeatmapZones;
  }
}

// ── Notifications ─────────────────────────────────────────────────────────────
export async function fetchNotifications(): Promise<Notification[]> {
  try {
    return await apiFetch<Notification[]>('/notifications');
  } catch {
    return mockNotifications;
  }
}

// ── Analytics ─────────────────────────────────────────────────────────────────
export async function fetchAnalytics(): Promise<AnalyticsData> {
  try {
    return await apiFetch<AnalyticsData>('/analytics/summary');
  } catch {
    return mockAnalytics;
  }
}

// ── Actions ───────────────────────────────────────────────────────────────────
export async function fetchActions(): Promise<Action[]> {
  try {
    return await apiFetch<Action[]>('/actions');
  } catch {
    return mockActions;
  }
}

// ── Dashboard live data ───────────────────────────────────────────────────────
export async function fetchDashboard() {
  try {
    return await apiFetch('/dashboard/summary');
  } catch {
    return null;
  }
}

// ── YOLO Live State (from Streamlit state files via backend) ──────────────────
export async function fetchLiveState() {
  try {
    return await apiFetch('/dashboard/live');
  } catch {
    return null;
  }
}
