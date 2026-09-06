from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.action import ActionItem
from app.models.incident import Incident
from app.models.evidence_timeline import EvidenceTimelineEvent
from app.schemas.action import ActionItemCreate, ActionItemUpdate
from app.core.errors import NotFoundException, ValidationAppException

VALID_ACTION_STATUSES = ["New", "Verified", "Assigned", "In Progress", "Resolved", "Rejected"]


class ActionService:
    @staticmethod
    def get_actions(
        db: Session,
        incident_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[ActionItem]:
        query = db.query(ActionItem)
        if incident_id:
            query = query.filter(ActionItem.incident_id == incident_id)
        if status:
            query = query.filter(ActionItem.status == status)
        return query.order_by(desc(ActionItem.created_at)).all()

    @staticmethod
    def create_action(db: Session, data: ActionItemCreate) -> ActionItem:
        incident = db.query(Incident).filter(Incident.id == data.incident_id).first()
        if not incident:
            raise NotFoundException(resource="Incident", identifier=data.incident_id)

        count = db.query(ActionItem).count() + 101
        action_code = f"ACT-{count}"

        action = ActionItem(
            action_code=action_code,
            incident_id=incident.id,
            title=data.title,
            priority=data.priority,
            assigned_team=data.assigned_team,
            status="Assigned",
            eta_minutes=data.eta_minutes or 30,
            notes=data.notes
        )
        db.add(action)

        # Sync Incident status
        if incident.status in ["New", "Under Review"]:
            incident.status = "Assigned"

        # Add timeline event
        timeline_event = EvidenceTimelineEvent(
            incident_id=incident.id,
            timestamp_str=datetime.utcnow().strftime("%I:%M:%S %p"),
            timestamp=datetime.utcnow(),
            event_type="Action Assigned",
            description=f"Action '{data.title}' dispatched to {data.assigned_team} with ETA of {data.eta_minutes or 30} mins.",
            is_ai_generated=False
        )
        db.add(timeline_event)

        db.commit()
        db.refresh(action)
        return action

    @staticmethod
    def update_action(db: Session, action_id: int, data: ActionItemUpdate) -> ActionItem:
        action = db.query(ActionItem).filter(ActionItem.id == action_id).first()
        if not action:
            raise NotFoundException(resource="ActionItem", identifier=action_id)

        if data.status:
            if data.status not in VALID_ACTION_STATUSES:
                raise ValidationAppException(f"Invalid action status '{data.status}'. Allowed: {', '.join(VALID_ACTION_STATUSES)}")
            action.status = data.status
            if data.status == "Resolved":
                action.resolved_at = datetime.utcnow()
                # Also resolve the linked incident
                incident = db.query(Incident).filter(Incident.id == action.incident_id).first()
                if incident:
                    incident.status = "Resolved"
                    incident.updated_at = datetime.utcnow()

        if data.priority:
            action.priority = data.priority
        if data.assigned_team:
            action.assigned_team = data.assigned_team
        if data.eta_minutes is not None:
            action.eta_minutes = data.eta_minutes
        if data.notes:
            action.notes = data.notes

        action.updated_at = datetime.utcnow()

        # Add timeline event
        timeline_event = EvidenceTimelineEvent(
            incident_id=action.incident_id,
            timestamp_str=datetime.utcnow().strftime("%I:%M:%S %p"),
            timestamp=datetime.utcnow(),
            event_type=f"Action Status: {action.status}",
            description=f"Action {action.action_code} updated. Status: {action.status}.",
            is_ai_generated=False
        )
        db.add(timeline_event)

        db.commit()
        db.refresh(action)
        return action


action_service = ActionService()
