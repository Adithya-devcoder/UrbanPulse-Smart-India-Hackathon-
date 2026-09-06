from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.models.road import Road, RoadSegment
from app.models.incident import Incident
from app.schemas.road import RoadResponse, RoadDetailResponse, RoadSegmentResponse
from app.schemas.common import APIResponse
from app.services.road_risk_service import road_risk_service
from app.core.errors import NotFoundException

router = APIRouter(prefix="/roads", tags=["Roads & Risk"])


@router.get("", response_model=APIResponse[List[RoadResponse]])
def list_roads(
    zone: Optional[str] = Query(None, description="Filter by zone"),
    status: Optional[str] = Query(None, description="Filter by risk status (High Risk, Moderate, Safe)"),
    db: Session = Depends(get_db)
):
    """List major urban roads and corridors with multi-factor risk scores."""
    query = db.query(Road)
    if zone:
        query = query.filter(Road.zone == zone)
    if status:
        query = query.filter(Road.status == status)

    roads = query.order_by(desc(Road.risk_score)).all()
    return APIResponse(
        success=True,
        message="Roads retrieved successfully",
        data=[RoadResponse.model_validate(r) for r in roads]
    )


@router.get("/{road_id}", response_model=APIResponse[RoadDetailResponse])
def get_road_detail(
    road_id: int = Path(..., description="Road ID"),
    db: Session = Depends(get_db)
):
    """Get detailed road risk breakdown including road segments and active incident counts."""
    road = db.query(Road).filter(Road.id == road_id).first()
    if not road:
        raise NotFoundException(resource="Road", identifier=road_id)

    segments = db.query(RoadSegment).filter(RoadSegment.road_id == road.id).all()
    active_incidents_count = db.query(Incident).filter(
        Incident.road_id == road.id,
        Incident.status.notin_(["Resolved", "Rejected"])
    ).count()

    detail = RoadDetailResponse(
        id=road.id,
        code=road.code,
        name=road.name,
        zone=road.zone,
        road_type=road.road_type,
        latitude=road.latitude,
        longitude=road.longitude,
        length_km=road.length_km,
        risk_score=road.risk_score,
        accident_count=road.accident_count,
        pothole_count=road.pothole_count,
        waterlogging_count=road.waterlogging_count,
        traffic_index=road.traffic_index,
        average_response_time_min=road.average_response_time_min,
        historical_trend=road.historical_trend,
        status=road.status,
        created_at=road.created_at,
        updated_at=road.updated_at,
        segments=[RoadSegmentResponse.model_validate(s) for s in segments],
        active_incidents_count=active_incidents_count
    )

    return APIResponse(
        success=True,
        message="Road details retrieved successfully",
        data=detail
    )


@router.post("/{road_id}/recalculate-risk", response_model=APIResponse[RoadResponse])
def recalculate_road_risk(
    road_id: int = Path(..., description="Road ID"),
    db: Session = Depends(get_db)
):
    """Trigger recalculation of dynamic risk score using multi-factor metrics."""
    road = road_risk_service.update_road_metrics(db, road_id)
    if not road:
        raise NotFoundException(resource="Road", identifier=road_id)

    return APIResponse(
        success=True,
        message=f"Risk score updated to {road.risk_score} (Status: {road.status})",
        data=RoadResponse.model_validate(road)
    )
