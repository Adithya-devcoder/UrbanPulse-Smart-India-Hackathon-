from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.models.vehicle import VehicleObservation
from app.schemas.vehicle import VehicleResponse
from app.schemas.common import APIResponse
from app.core.errors import NotFoundException

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.get("", response_model=APIResponse[List[VehicleResponse]])
def list_vehicles(
    incident_id: Optional[int] = Query(None, description="Filter by incident ID"),
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type"),
    has_plate: Optional[bool] = Query(None, description="Filter only vehicles with detected license plate"),
    db: Session = Depends(get_db)
):
    """List tracked vehicles and ANPR license plate observations."""
    query = db.query(VehicleObservation)
    if incident_id:
        query = query.filter(VehicleObservation.incident_id == incident_id)
    if vehicle_type:
        query = query.filter(VehicleObservation.vehicle_type == vehicle_type)
    if has_plate is True:
        query = query.filter(VehicleObservation.license_plate.isnot(None))
    elif has_plate is False:
        query = query.filter(VehicleObservation.license_plate.is_(None))

    vehicles = query.order_by(desc(VehicleObservation.created_at)).limit(50).all()
    return APIResponse(
        success=True,
        message="Vehicles retrieved successfully",
        data=[VehicleResponse.model_validate(v) for v in vehicles]
    )


@router.get("/{vehicle_id}", response_model=APIResponse[VehicleResponse])
def get_vehicle_detail(
    vehicle_id: int = Path(..., description="Vehicle Observation ID"),
    db: Session = Depends(get_db)
):
    """Retrieve detailed vehicle observation."""
    veh = db.query(VehicleObservation).filter(VehicleObservation.id == vehicle_id).first()
    if not veh:
        raise NotFoundException(resource="Vehicle", identifier=vehicle_id)

    return APIResponse(
        success=True,
        message="Vehicle details retrieved successfully",
        data=VehicleResponse.model_validate(veh)
    )
