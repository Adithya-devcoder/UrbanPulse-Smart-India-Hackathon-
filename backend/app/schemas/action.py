from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ActionItemCreate(BaseModel):
    incident_id: int
    title: str
    priority: str = Field("High", description="Low, Medium, High, Critical")
    assigned_team: str = Field("Traffic Police Unit", description="Team/Unit name")
    eta_minutes: Optional[int] = 30
    notes: Optional[str] = None


class ActionItemUpdate(BaseModel):
    status: Optional[str] = Field(None, description="New, Verified, Assigned, In Progress, Resolved, Rejected")
    priority: Optional[str] = None
    assigned_team: Optional[str] = None
    eta_minutes: Optional[int] = None
    notes: Optional[str] = None


class ActionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_code: str
    incident_id: int
    title: str
    priority: str
    assigned_team: str
    status: str
    eta_minutes: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
