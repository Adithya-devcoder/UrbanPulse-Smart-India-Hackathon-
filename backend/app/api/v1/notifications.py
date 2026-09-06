from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.notification import NotificationResponse
from app.schemas.common import APIResponse
from app.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=APIResponse[List[NotificationResponse]])
def list_notifications(
    unread_only: bool = Query(False, description="Filter only unread alerts"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List system and critical alert notifications."""
    notifs = notification_service.get_notifications(db, unread_only=unread_only, limit=limit)
    return APIResponse(
        success=True,
        message="Notifications retrieved successfully",
        data=[NotificationResponse.model_validate(n) for n in notifs]
    )


@router.patch("/{notification_id}/read", response_model=APIResponse[NotificationResponse])
def mark_notification_read(
    notification_id: int = Path(..., description="Notification ID"),
    db: Session = Depends(get_db)
):
    """Mark single notification as read."""
    notif = notification_service.mark_as_read(db, notification_id)
    return APIResponse(
        success=True,
        message="Notification marked as read",
        data=NotificationResponse.model_validate(notif)
    )


@router.post("/mark-all-read", response_model=APIResponse[dict])
def mark_all_notifications_read(db: Session = Depends(get_db)):
    """Mark all notifications as read."""
    count = notification_service.mark_all_as_read(db)
    return APIResponse(
        success=True,
        message=f"{count} notifications marked as read",
        data={"updated_count": count}
    )
