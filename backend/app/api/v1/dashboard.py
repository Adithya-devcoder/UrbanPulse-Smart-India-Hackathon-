from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import DashboardKPIsResponse
from app.schemas.common import APIResponse
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/kpis", response_model=APIResponse[DashboardKPIsResponse])
def get_dashboard_kpis(db: Session = Depends(get_db)):
    """
    Get live dashboard KPIs for the UrbanPulse central dashboard:
    Active Incidents, High-Risk Roads, Potholes Detected, Waterlogging Zones,
    AI Detections, Resolved Incidents, Active Buses, and Active Cameras.
    """
    kpis = analytics_service.get_dashboard_kpis(db)
    return APIResponse(
        success=True,
        message="Dashboard KPIs retrieved successfully",
        data=kpis
    )


@router.get("/summary", response_model=APIResponse[DashboardKPIsResponse])
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Alias for dashboard summary."""
    kpis = analytics_service.get_dashboard_kpis(db)
    return APIResponse(
        success=True,
        message="Dashboard summary retrieved successfully",
        data=kpis
    )
