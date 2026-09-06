from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base


class Road(Base):
    __tablename__ = "roads"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), index=True, nullable=False)
    zone = Column(String(100), nullable=True)
    road_type = Column(String(50), default="Arterial")  # Arterial, Highway, Commercial, Residential
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    length_km = Column(Float, default=5.0)
    
    # Dynamic Risk & Metric Fields
    risk_score = Column(Float, default=0.0)  # 0.0 - 100.0
    accident_count = Column(Integer, default=0)
    pothole_count = Column(Integer, default=0)
    waterlogging_count = Column(Integer, default=0)
    traffic_index = Column(Float, default=50.0)  # 0 - 100
    average_response_time_min = Column(Float, default=25.0)
    historical_trend = Column(String(20), default="stable")  # improving, stable, worsening
    status = Column(String(50), default="Moderate")  # High Risk, Moderate, Safe

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    incidents = relationship("Incident", back_populates="road", cascade="all, delete-orphan")


class RoadSegment(Base):
    __tablename__ = "road_segments"

    id = Column(Integer, primary_key=True, index=True)
    road_id = Column(Integer, index=True, nullable=False)
    segment_name = Column(String(200), nullable=False)
    start_latitude = Column(Float, nullable=False)
    start_longitude = Column(Float, nullable=False)
    end_latitude = Column(Float, nullable=False)
    end_longitude = Column(Float, nullable=False)
    current_density = Column(Float, default=0.0)
    avg_speed_kmh = Column(Float, default=30.0)
    is_bottleneck = Column(Integer, default=0)  # 0 = False, 1 = True
    delay_minutes = Column(Float, default=0.0)
