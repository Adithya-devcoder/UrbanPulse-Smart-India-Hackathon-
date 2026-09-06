from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EvidenceFrameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    frame_number: int
    camera_id: str
    file_url: str
    mime_type: str
    timestamp: datetime
    bounding_boxes: Optional[Any] = None
    ocr_extracted_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    caption: Optional[str] = None


class EvidenceTimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    evidence_frame_id: Optional[int] = None
    timestamp_str: str
    timestamp: datetime
    event_type: str
    description: str
    vehicle_track_id: Optional[str] = None
    is_ai_generated: bool
