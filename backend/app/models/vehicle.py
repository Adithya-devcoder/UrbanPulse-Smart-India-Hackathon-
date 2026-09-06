from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class VehicleObservation(Base):
    __tablename__ = "vehicle_observations"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True, index=True)
    observation_id = Column(Integer, ForeignKey("observations.id"), nullable=True)
    
    vehicle_track_id = Column(String(50), nullable=False)  # e.g., "Vehicle A", "TRK-092"
    vehicle_type = Column(String(50), default="car")       # car, bike, bus, truck, auto, other
    color = Column(String(50), nullable=True)             # Silver, Black, White
    license_plate = Column(String(50), nullable=True)     # "TN 09 BX 4412" (OCR or AI derived)
    plate_confidence = Column(Float, nullable=True)
    
    speed_kmh = Column(Float, nullable=True)
    direction = Column(String(50), nullable=True)         # Northbound, Southbound
    lane = Column(String(50), nullable=True)              # Lane 1, Lane 2, Bus Lane
    confidence = Column(Float, default=0.90)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    incident = relationship("Incident", back_populates="vehicles")
