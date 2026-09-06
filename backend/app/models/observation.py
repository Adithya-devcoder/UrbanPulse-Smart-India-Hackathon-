from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True, index=True)
    module = Column(String(50), nullable=False)
    
    # Module specific observation details
    defect_type = Column(String(100), nullable=True)  # e.g., pothole_deep, alligator_crack
    sign_type = Column(String(100), nullable=True)    # e.g., STOP, SPEED_LIMIT_40
    sign_condition = Column(String(50), nullable=True) # damaged, missing, illegible
    pedestrian_movement = Column(String(100), nullable=True) # crossing_jaywalk, curb_waiting
    risk_state = Column(String(50), nullable=True)    # LOW, MEDIUM, HIGH
    
    confidence = Column(Float, nullable=False, default=0.8)
    camera_id = Column(String(50), nullable=False)
    bus_id = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    raw_metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    incident = relationship("Incident", back_populates="observations")
