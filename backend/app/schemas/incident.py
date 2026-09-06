from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.evidence import EvidenceFrameResponse, EvidenceTimelineEventResponse
from app.schemas.vehicle import VehicleResponse


class IncidentStatusUpdate(BaseModel):
    status: str = Field(..., description="New, Under Review, Verified, Assigned, Monitoring, In Progress, Resolved, Rejected")
    notes: Optional[str] = None


class IncidentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_code: str
    incident_type: str
    module: str
    road_id: Optional[int] = None
    location_name: str
    latitude: float
    longitude: float
    severity: str
    confidence: float
    status: str
    detected_time: datetime
    waterlogged_pothole_probability: Optional[float] = None
    evidence_count: int = 0
    vehicles_count: int = 0
    created_at: datetime


class IncidentDetailResponse(IncidentListItem):
    model_config = ConfigDict(from_attributes=True)

    assessment_text: Optional[str] = None
    evidence_frames: List[EvidenceFrameResponse] = []
    timeline_events: List[EvidenceTimelineEventResponse] = []
    vehicles: List[VehicleResponse] = []
