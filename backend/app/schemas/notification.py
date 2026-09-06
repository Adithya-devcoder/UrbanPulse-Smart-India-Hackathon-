from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: Optional[int] = None
    notification_type: str
    title: str
    message: str
    severity: str
    is_read: bool
    created_at: datetime
