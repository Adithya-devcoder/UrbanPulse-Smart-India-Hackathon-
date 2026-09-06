from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base


class EvidenceTimelineEvent(Base):
    __tablename__ = "evidence_timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    evidence_frame_id = Column(Integer, ForeignKey("evidence_frames.id"), nullable=True)
    
    timestamp_str = Column(String(50), nullable=False)  # e.g., "10:42:18 AM"
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    vehicle_track_id = Column(String(50), nullable=True)
    is_ai_generated = Column(Boolean, default=True)

    # Relationships
    incident = relationship("Incident", back_populates="timeline_events")
    evidence_frame = relationship("EvidenceFrame", back_populates="timeline_events")
