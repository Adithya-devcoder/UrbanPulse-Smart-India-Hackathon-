from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.search import UnifiedSearchResponse
from app.schemas.common import APIResponse
from app.services.search_service import search_service

router = APIRouter(prefix="/search", tags=["Global Search"])


@router.get("", response_model=APIResponse[UnifiedSearchResponse])
def global_search(
    q: str = Query(..., min_length=1, description="Search term for incidents, roads, vehicles, and cameras"),
    db: Session = Depends(get_db)
):
    """
    Unified global search across:
    - Incidents (e.g., 'INC-2048', 'Hit-and-run', 'Anna Salai')
    - Roads (e.g., 'Anna Salai', 'OMR', 'GST')
    - Vehicles & Plates (e.g., 'TN 09 BX 4412', 'Vehicle A')
    - Cameras (e.g., 'CAM-042')
    """
    result = search_service.search_all(db, q)
    return APIResponse(
        success=True,
        message=f"Found {result.total_results} matching results",
        data=result
    )
