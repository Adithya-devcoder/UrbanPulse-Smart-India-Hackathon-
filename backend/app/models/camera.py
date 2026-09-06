from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base


class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    bus_number = Column(String(50), unique=True, index=True, nullable=False)
    route_number = Column(String(50), index=True, nullable=False)
    status = Column(String(50), default="Active")  # Active, In Transit, Maintenance, Idle
    last_latitude = Column(Float, nullable=True)
    last_longitude = Column(Float, nullable=True)
    last_ping_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cameras = relationship("Camera", back_populates="bus", cascade="all, delete-orphan")


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    camera_code = Column(String(50), unique=True, index=True, nullable=False)  # e.g., CAM-042
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=True)
    camera_position = Column(String(50), default="front")  # front, rear, left_side, right_side
    location_name = Column(String(200), default="Anna Salai")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String(50), default="Online")  # Online, Offline, Warning
    last_frame_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bus = relationship("Bus", back_populates="cameras")
