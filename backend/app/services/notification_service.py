from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.notification import Notification
from app.core.errors import NotFoundException


class NotificationService:
    @staticmethod
    def get_notifications(db: Session, unread_only: bool = False, limit: int = 50) -> List[Notification]:
        query = db.query(Notification)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        return query.order_by(desc(Notification.created_at)).limit(limit).all()

    @staticmethod
    def mark_as_read(db: Session, notification_id: int) -> Notification:
        notif = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notif:
            raise NotFoundException(resource="Notification", identifier=notification_id)
        notif.is_read = True
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def mark_all_as_read(db: Session) -> int:
        updated_count = db.query(Notification).filter(Notification.is_read == False).update({"is_read": True})
        db.commit()
        return updated_count

    @staticmethod
    def create_notification(
        db: Session,
        title: str,
        message: str,
        notification_type: str = "CRITICAL_ALERT",
        severity: str = "Medium",
        incident_id: Optional[int] = None
    ) -> Notification:
        notif = Notification(
            incident_id=incident_id,
            notification_type=notification_type,
            title=title,
            message=message,
            severity=severity,
            is_read=False
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif


notification_service = NotificationService()
