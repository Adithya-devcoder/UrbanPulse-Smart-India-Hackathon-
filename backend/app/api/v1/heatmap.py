from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.heatmap import HeatmapResponse
from app.schemas.common import APIResponse
from app.services.heatmap_service import heatmap_service

router = APIRouter(prefix="/heatmap", tags=["Risk Heatmap"])


@router.get("", response_model=APIResponse[HeatmapResponse])
def get_risk_heatmap(
    time_range: str = Query("7_days", description="today | 7_days | 30_days | 3_months"),
    risk_type: str = Query("all", description="all | accidents | potholes | waterlogging | traffic | infrastructure"),
    db: Session = Depends(get_db)
):
    """
    Retrieve geographic aggregated risk points and heat intensities for map visualization.
    Allows filtering across temporal ranges and risk categories.
    """
    result = heatmap_service.get_heatmap_points(
        db=db,
        time_range=time_range,
        risk_type=risk_type
    )
    return APIResponse(
        success=True,
        message="Heatmap data retrieved successfully",
        data=result
    )
