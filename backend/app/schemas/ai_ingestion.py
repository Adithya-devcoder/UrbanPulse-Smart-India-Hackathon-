from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class BoundingBox(BaseModel):
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    box: List[float] = Field(..., description="[x_min, y_min, x_max, y_max] or [x, y, w, h]")


class VehicleDetectionInfo(BaseModel):
    track_id: Optional[str] = None
    vehicle_type: Optional[str] = "car"  # car, bike, bus, truck, auto, other
    color: Optional[str] = None
    license_plate: Optional[str] = None
    plate_confidence: Optional[float] = None
    speed_kmh: Optional[float] = None
    direction: Optional[str] = None
    lane: Optional[str] = None
    confidence: float = Field(0.9, ge=0.0, le=1.0)


class AIDetectionIngestRequest(BaseModel):
    module: str = Field(
        ...,
        description="road_defect | traffic_sign | vehicle_density | traffic_bottleneck | vulnerable_pedestrian | multimodal"
    )
    incident_type: Optional[str] = Field(
        None,
        description="Pothole / Road Defect, Damaged / Missing Traffic Sign, etc."
    )
    bus_id: str = Field(..., description="Bus identifier e.g. BUS-104")
    camera_id: str = Field(..., description="Camera identifier e.g. CAM-042")
    camera_position: Optional[str] = Field("front", description="front, rear, left_side, right_side")
    
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    location_name: Optional[str] = Field(None, description="Nearby road/landmark name")
    
    confidence: float = Field(0.85, ge=0.0, le=1.0)
    severity: Optional[str] = Field("Medium", description="Low, Medium, High, Critical")
    
    # Module-specific fields
    defect_type: Optional[str] = Field(None, description="pothole_deep, crack, rutting, etc.")
    defect_size_cm: Optional[float] = Field(None, description="Approximate defect diameter")
    
    sign_type: Optional[str] = Field(None, description="STOP, SPEED_LIMIT_40, NO_ENTRY, etc.")
    sign_condition: Optional[str] = Field(None, description="damaged, missing, illegible, obscured")
    
    pedestrian_track_id: Optional[str] = None
    pedestrian_movement: Optional[str] = Field(None, description="crossing_jaywalk, waiting_curb, walking_along_traffic")
    risk_level: Optional[str] = Field(None, description="LOW, MEDIUM, HIGH")
    
    # Traffic & Density fields
    traffic_density: Optional[float] = Field(None, description="Vehicles per km or density ratio")
    average_speed_kmh: Optional[float] = None
    delay_seconds: Optional[float] = None
    
    vehicles: Optional[List[VehicleDetectionInfo]] = None
    bounding_boxes: Optional[List[BoundingBox]] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("module")
    def validate_module(cls, v):
        allowed = {
            "road_defect", "traffic_sign", "vehicle_density",
            "traffic_bottleneck", "vulnerable_pedestrian", "multimodal",
            "pothole", "pedestrian", "bottleneck"
        }
        if v.lower() not in allowed:
            raise ValueError(f"Module must be one of: {', '.join(sorted(allowed))}")
        return v.lower()


class AIDetectionIngestResponse(BaseModel):
    incident_id: int
    incident_code: str
    incident_type: str
    status: str
    module: str
    is_correlated: bool
    evidence_frame_id: Optional[int] = None
    evidence_url: Optional[str] = None
    ocr_extracted_text: Optional[str] = None
    waterlogged_pothole_probability: Optional[float] = None
    message: str
