from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RoadSegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    road_id: int
    segment_name: str
    start_latitude: float
    start_longitude: float
    end_latitude: float
    end_longitude: float
    current_density: float
    avg_speed_kmh: float
    is_bottleneck: int
    delay_minutes: float


class RoadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    zone: Optional[str] = None
    road_type: str
    latitude: float
    longitude: float
    length_km: float
    risk_score: float
    accident_count: int
    pothole_count: int
    waterlogging_count: int
    traffic_index: float
    average_response_time_min: float
    historical_trend: str
    status: str
    created_at: datetime
    updated_at: datetime


class RoadDetailResponse(RoadResponse):
    model_config = ConfigDict(from_attributes=True)

    segments: List[RoadSegmentResponse] = []
    active_incidents_count: int = 0
