from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.camera import Camera, Bus
from app.schemas.camera import CameraResponse, BusResponse
from app.schemas.common import APIResponse
from app.core.errors import NotFoundException

router = APIRouter(prefix="", tags=["Cameras & Fleet"])


@router.get("/cameras", response_model=APIResponse[List[CameraResponse]])
def list_cameras(
    status: Optional[str] = Query(None, description="Filter by camera status (Online, Offline)"),
    db: Session = Depends(get_db)
):
    """List bus-mounted cameras deployed across the mobile sensing fleet."""
    query = db.query(Camera)
    if status:
        query = query.filter(Camera.status == status)
    cameras = query.all()
    return APIResponse(
        success=True,
        message="Cameras retrieved successfully",
        data=[CameraResponse.model_validate(c) for c in cameras]
    )


@router.get("/cameras/{identifier}", response_model=APIResponse[CameraResponse])
def get_camera(
    identifier: str = Path(..., description="Camera ID or code (e.g., 'CAM-042')"),
    db: Session = Depends(get_db)
):
    """Retrieve specific camera status and latest frame metadata."""
    if identifier.isdigit():
        cam = db.query(Camera).filter(Camera.id == int(identifier)).first()
    else:
        cam = db.query(Camera).filter(Camera.camera_code == identifier).first()

    if not cam:
        raise NotFoundException(resource="Camera", identifier=identifier)

    return APIResponse(
        success=True,
        message="Camera details retrieved successfully",
        data=CameraResponse.model_validate(cam)
    )


@router.get("/buses", response_model=APIResponse[List[BusResponse]])
def list_buses(db: Session = Depends(get_db)):
    """List mobile urban sensing buses and their onboard camera configurations."""
    buses = db.query(Bus).all()
    res = []
    for b in buses:
        b_cameras = db.query(Camera).filter(Camera.bus_id == b.id).all()
        res.append(BusResponse(
            id=b.id,
            bus_number=b.bus_number,
            route_number=b.route_number,
            status=b.status,
            last_latitude=b.last_latitude,
            last_longitude=b.last_longitude,
            last_ping_at=b.last_ping_at,
            cameras=[CameraResponse.model_validate(c) for c in b_cameras]
        ))
    return APIResponse(
        success=True,
        message="Buses retrieved successfully",
        data=res
    )
