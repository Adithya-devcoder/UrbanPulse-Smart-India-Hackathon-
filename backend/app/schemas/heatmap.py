from typing import List, Optional
from pydantic import BaseModel


class HeatmapPoint(BaseModel):
    latitude: float
    longitude: float
    weight: float  # Normalized intensity 0.0 - 1.0
    risk_type: str  # accidents, potholes, waterlogging, traffic, infrastructure
    incident_code: Optional[str] = None
    severity: str
    location_name: str


class HeatmapResponse(BaseModel):
    time_range: str
    risk_type: str
    total_points: int
    points: List[HeatmapPoint]
