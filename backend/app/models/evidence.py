from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class EvidenceFrame(Base):
    __tablename__ = "evidence_frames"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    observation_id = Column(Integer, ForeignKey("observations.id"), nullable=True)
    frame_number = Column(Integer, default=1)
    camera_id = Column(String(50), nullable=False)
    
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=False)
    mime_type = Column(String(50), default="image/jpeg")
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    bounding_boxes = Column(JSON, nullable=True)  # [{label: 'car', bbox: [x,y,w,h], confidence: 0.9}]
    ocr_extracted_text = Column(String(255), nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    caption = Column(String(255), nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="evidence_frames")
    timeline_events = relationship("EvidenceTimelineEvent", back_populates="evidence_frame")
