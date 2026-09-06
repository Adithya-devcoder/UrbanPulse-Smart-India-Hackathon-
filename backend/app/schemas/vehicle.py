from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: Optional[int] = None
    vehicle_track_id: str
    vehicle_type: str
    color: Optional[str] = None
    license_plate: Optional[str] = None
    plate_confidence: Optional[float] = None
    speed_kmh: Optional[float] = None
    direction: Optional[str] = None
    lane: Optional[str] = None
    confidence: float
    created_at: datetime
