from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    TrendPoint,
    AIPerformanceStats
)
from app.schemas.common import APIResponse
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics & Reports"])


@router.get("/overview", response_model=APIResponse[AnalyticsOverviewResponse])
def get_analytics_overview(
    time_range: str = Query("7_days", description="7_days | 30_days | 90_days"),
    db: Session = Depends(get_db)
):
    """Retrieve comprehensive urban road analytics: trends, distributions, response times, and AI accuracy."""
    overview = analytics_service.get_overview(db, time_range=time_range)
    return APIResponse(
        success=True,
        message="Analytics overview retrieved successfully",
        data=overview
    )


@router.get("/trends", response_model=APIResponse[List[TrendPoint]])
def get_incident_trends(
    time_range: str = Query("7_days", description="7_days | 30_days | 90_days"),
    db: Session = Depends(get_db)
):
    """Retrieve historical daily incident trends."""
    overview = analytics_service.get_overview(db, time_range=time_range)
    return APIResponse(
        success=True,
        message="Incident trends retrieved successfully",
        data=overview.trends
    )


@router.get("/ai-performance", response_model=APIResponse[AIPerformanceStats])
def get_ai_performance(db: Session = Depends(get_db)):
    """Retrieve AI detection statistics, average confidence, and per-module breakdown."""
    overview = analytics_service.get_overview(db)
    return APIResponse(
        success=True,
        message="AI performance statistics retrieved successfully",
        data=overview.ai_performance
    )
