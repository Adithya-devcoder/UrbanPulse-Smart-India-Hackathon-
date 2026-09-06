from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    action_code = Column(String(50), unique=True, index=True, nullable=False)  # e.g., ACT-2048
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    priority = Column(String(50), default="High")  # Low, Medium, High, Critical
    assigned_team = Column(String(100), default="Traffic Police Unit")
    status = Column(String(50), default="New", index=True)  # New, Verified, Assigned, In Progress, Resolved, Rejected
    
    eta_minutes = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="actions")
