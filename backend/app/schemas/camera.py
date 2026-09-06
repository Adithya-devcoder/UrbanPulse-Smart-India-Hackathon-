from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CameraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    camera_code: str
    bus_id: Optional[int] = None
    camera_position: str
    location_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str
    last_frame_at: datetime


class BusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bus_number: str
    route_number: str
    status: str
    last_latitude: Optional[float] = None
    last_longitude: Optional[float] = None
    last_ping_at: datetime
    cameras: List[CameraResponse] = []
