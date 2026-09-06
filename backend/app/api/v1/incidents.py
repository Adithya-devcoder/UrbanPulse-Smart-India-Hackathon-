from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.incident import IncidentListItem, IncidentDetailResponse, IncidentStatusUpdate
from app.schemas.evidence import EvidenceFrameResponse, EvidenceTimelineEventResponse
from app.schemas.vehicle import VehicleResponse
from app.schemas.common import APIResponse, PaginatedData
from app.services.incident_service import incident_service
from app.services.pdf_report_service import pdf_report_service
from app.models.evidence import EvidenceFrame
from app.models.evidence_timeline import EvidenceTimelineEvent
from app.models.vehicle import VehicleObservation

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=APIResponse[PaginatedData[IncidentListItem]])
def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status (New, Under Review, Verified, Assigned, Monitoring, In Progress, Resolved, Rejected)"),
    module: Optional[str] = Query(None, description="Filter by module (road_defect, traffic_sign, vehicle_density, traffic_bottleneck, vulnerable_pedestrian)"),
    severity: Optional[str] = Query(None, description="Filter by severity (Low, Medium, High, Critical)"),
    road_id: Optional[int] = Query(None, description="Filter by road ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List road incidents with optional filters and pagination."""
    items, total = incident_service.get_incidents(
        db=db,
        status=status,
        module=module,
        severity=severity,
        road_id=road_id,
        page=page,
        page_size=page_size
    )
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

    return APIResponse(
        success=True,
        message="Incidents retrieved successfully",
        data=PaginatedData(
            items=[IncidentListItem(**it) for it in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.get("/{identifier}", response_model=APIResponse[IncidentDetailResponse])
def get_incident_detail(
    identifier: str = Path(..., description="Incident ID or code (e.g., 'INC-2048' or '1')"),
    db: Session = Depends(get_db)
):
    """Retrieve full incident dossier including multi-camera frames, timeline events, and vehicle intel."""
    incident = incident_service.get_incident_by_identifier(db, identifier)
    
    evidence_frames = db.query(EvidenceFrame).filter(EvidenceFrame.incident_id == incident.id).all()
    timeline_events = db.query(EvidenceTimelineEvent).filter(EvidenceTimelineEvent.incident_id == incident.id).order_by(EvidenceTimelineEvent.timestamp).all()
    vehicles = db.query(VehicleObservation).filter(VehicleObservation.incident_id == incident.id).all()

    detail = IncidentDetailResponse(
        id=incident.id,
        incident_code=incident.incident_code,
        incident_type=incident.incident_type,
        module=incident.module,
        road_id=incident.road_id,
        location_name=incident.location_name,
        latitude=incident.latitude,
        longitude=incident.longitude,
        severity=incident.severity,
        confidence=incident.confidence,
        status=incident.status,
        detected_time=incident.detected_time,
        waterlogged_pothole_probability=incident.waterlogged_pothole_probability,
        evidence_count=len(evidence_frames),
        vehicles_count=len(vehicles),
        created_at=incident.created_at,
        assessment_text=incident.assessment_text,
        evidence_frames=[EvidenceFrameResponse.model_validate(f) for f in evidence_frames],
        timeline_events=[EvidenceTimelineEventResponse.model_validate(t) for t in timeline_events],
        vehicles=[VehicleResponse.model_validate(v) for v in vehicles]
    )

    return APIResponse(
        success=True,
        message="Incident details retrieved successfully",
        data=detail
    )


@router.patch("/{identifier}/status", response_model=APIResponse[IncidentListItem])
def update_incident_status(
    payload: IncidentStatusUpdate,
    identifier: str = Path(..., description="Incident ID or code (e.g. 'INC-2048')"),
    db: Session = Depends(get_db)
):
    """Update incident status (e.g. New -> Under Review -> Verified -> Assigned -> Resolved)."""
    incident = incident_service.update_status(
        db=db,
        identifier=identifier,
        new_status=payload.status,
        notes=payload.notes
    )
    return APIResponse(
        success=True,
        message=f"Incident status updated to '{incident.status}'",
        data=IncidentListItem.model_validate(incident)
    )


@router.get("/{identifier}/evidence", response_model=APIResponse[dict])
def get_incident_evidence(
    identifier: str = Path(..., description="Incident ID or code"),
    db: Session = Depends(get_db)
):
    """Retrieve evidence frames and timeline events for an incident."""
    incident = incident_service.get_incident_by_identifier(db, identifier)
    frames = db.query(EvidenceFrame).filter(EvidenceFrame.incident_id == incident.id).all()
    timeline = db.query(EvidenceTimelineEvent).filter(EvidenceTimelineEvent.incident_id == incident.id).order_by(EvidenceTimelineEvent.timestamp).all()

    return APIResponse(
        success=True,
        message="Evidence retrieved successfully",
        data={
            "incident_code": incident.incident_code,
            "evidence_frames": [EvidenceFrameResponse.model_validate(f) for f in frames],
            "timeline_events": [EvidenceTimelineEventResponse.model_validate(t) for t in timeline]
        }
    )


@router.get("/{identifier}/export")
def export_incident_pdf(
    identifier: str = Path(..., description="Incident ID or code (e.g. 'INC-2048')"),
    db: Session = Depends(get_db)
):
    """
    Generate and stream an official UrbanPulse PDF incident dossier report with
    AI assessment notice, vehicle intelligence, OCR extraction, and evidence timeline.
    """
    pdf_buffer = pdf_report_service.generate_incident_pdf(db, identifier)
    filename = f"UrbanPulse_Incident_{identifier}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )
