from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_code = Column(String(50), unique=True, index=True, nullable=False)  # e.g., INC-2048
    incident_type = Column(String(100), index=True, nullable=False)
    module = Column(String(50), index=True, nullable=False)  # road_defect, traffic_sign, vehicle_density, traffic_bottleneck, vulnerable_pedestrian, multimodal
    
    road_id = Column(Integer, ForeignKey("roads.id"), nullable=True)
    location_name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    
    severity = Column(String(50), default="Medium", index=True)  # Low, Medium, High, Critical
    confidence = Column(Float, default=0.85)  # 0.0 - 1.0 (e.g. 0.87 for 87%)
    status = Column(String(50), default="New", index=True)  # New, Under Review, Verified, Assigned, Monitoring, In Progress, Resolved, Rejected
    
    detected_time = Column(DateTime, default=datetime.utcnow, index=True)
    assessment_text = Column(Text, nullable=True)  # AI-generated event reconstruction
    waterlogged_pothole_probability = Column(Float, nullable=True)  # 0.0 - 1.0
    is_demo_seed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    road = relationship("Road", back_populates="incidents")
    observations = relationship("Observation", back_populates="incident", cascade="all, delete-orphan")
    evidence_frames = relationship("EvidenceFrame", back_populates="incident", cascade="all, delete-orphan")
    timeline_events = relationship("EvidenceTimelineEvent", back_populates="incident", cascade="all, delete-orphan")
    vehicles = relationship("VehicleObservation", back_populates="incident", cascade="all, delete-orphan")
    actions = relationship("ActionItem", back_populates="incident", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="incident", cascade="all, delete-orphan")
