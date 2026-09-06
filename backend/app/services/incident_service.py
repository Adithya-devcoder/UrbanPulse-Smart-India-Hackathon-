from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.incident import Incident
from app.models.evidence import EvidenceFrame
from app.models.evidence_timeline import EvidenceTimelineEvent
from app.models.vehicle import VehicleObservation
from app.core.errors import NotFoundException, ValidationAppException

VALID_INCIDENT_STATUSES = [
    "New", "Under Review", "Verified", "Assigned",
    "Monitoring", "In Progress", "Resolved", "Rejected"
]


class IncidentService:
    @staticmethod
    def get_incidents(
        db: Session,
        status: Optional[str] = None,
        module: Optional[str] = None,
        severity: Optional[str] = None,
        road_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        query = db.query(Incident)

        if status:
            query = query.filter(Incident.status == status)
        if module:
            query = query.filter(Incident.module == module)
        if severity:
            query = query.filter(Incident.severity == severity)
        if road_id:
            query = query.filter(Incident.road_id == road_id)

        total = query.count()
        incidents = query.order_by(desc(Incident.detected_time))\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()

        items = []
        for inc in incidents:
            evidence_count = db.query(EvidenceFrame).filter(EvidenceFrame.incident_id == inc.id).count()
            vehicles_count = db.query(VehicleObservation).filter(VehicleObservation.incident_id == inc.id).count()
            items.append({
                "id": inc.id,
                "incident_code": inc.incident_code,
                "incident_type": inc.incident_type,
                "module": inc.module,
                "road_id": inc.road_id,
                "location_name": inc.location_name,
                "latitude": inc.latitude,
                "longitude": inc.longitude,
                "severity": inc.severity,
                "confidence": inc.confidence,
                "status": inc.status,
                "detected_time": inc.detected_time,
                "waterlogged_pothole_probability": inc.waterlogged_pothole_probability,
                "evidence_count": evidence_count,
                "vehicles_count": vehicles_count,
                "created_at": inc.created_at
            })

        return items, total

    @staticmethod
    def get_incident_by_identifier(db: Session, identifier: str) -> Incident:
        """Finds incident by integer ID or string code (e.g. 'INC-2048' or '2048')"""
        if identifier.isdigit():
            incident = db.query(Incident).filter(Incident.id == int(identifier)).first()
            if incident:
                return incident
        
        # Query by incident_code
        incident = db.query(Incident).filter(Incident.incident_code == identifier).first()
        if not incident:
            # Try prepending 'INC-'
            incident = db.query(Incident).filter(Incident.incident_code == f"INC-{identifier}").first()

        if not incident:
            raise NotFoundException(resource="Incident", identifier=identifier)
        return incident

    @staticmethod
    def update_status(db: Session, identifier: str, new_status: str, notes: Optional[str] = None) -> Incident:
        incident = IncidentService.get_incident_by_identifier(db, identifier)
        if new_status not in VALID_INCIDENT_STATUSES:
            raise ValidationAppException(
                f"Invalid status '{new_status}'. Allowed: {', '.join(VALID_INCIDENT_STATUSES)}"
            )

        old_status = incident.status
        incident.status = new_status
        incident.updated_at = datetime.utcnow()

        # Add timeline event for status transition
        timeline_event = EvidenceTimelineEvent(
            incident_id=incident.id,
            timestamp_str=datetime.utcnow().strftime("%I:%M:%S %p"),
            timestamp=datetime.utcnow(),
            event_type="Status Updated",
            description=f"Incident status changed from '{old_status}' to '{new_status}'. {notes or ''}".strip(),
            is_ai_generated=False
        )
        db.add(timeline_event)
        db.commit()
        db.refresh(incident)
        return incident


incident_service = IncidentService()
