from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True, index=True)
    
    notification_type = Column(String(50), nullable=False)  # CRITICAL_ALERT, INCIDENT_NEW, ACTION_ASSIGNED, RISK_SURGE
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(50), default="Medium")  # Low, Medium, High, Critical
    is_read = Column(Boolean, default=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    incident = relationship("Incident", back_populates="notifications")
