from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DashboardKPIsResponse(BaseModel):
    active_incidents: int
    high_risk_roads: int
    potholes_detected: int
    waterlogging_zones: int
    ai_detections_today: int
    resolved_incidents: int
    active_buses: int
    active_cameras: int
    system_health: str = "Optimal"


class TrendPoint(BaseModel):
    date: str
    potholes: int
    traffic_incidents: int
    pedestrian_risks: int
    signs_defects: int
    total: int


class IncidentDistribution(BaseModel):
    category: str
    count: int
    percentage: float


class ResponsePerformance(BaseModel):
    avg_response_time_min: float
    resolution_rate_percent: float
    critical_incident_sla_percent: float
    resolved_this_week: int
    pending_dispatch: int


class AIPerformanceStats(BaseModel):
    total_detections: int
    avg_confidence: float
    detection_accuracy_rate: float
    false_positive_rate: float
    module_breakdown: Dict[str, int]


class AnalyticsOverviewResponse(BaseModel):
    time_range: str
    kpis: DashboardKPIsResponse
    trends: List[TrendPoint]
    distribution: List[IncidentDistribution]
    response_performance: ResponsePerformance
    ai_performance: AIPerformanceStats
