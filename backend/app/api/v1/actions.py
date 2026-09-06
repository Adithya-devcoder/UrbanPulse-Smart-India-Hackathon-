from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.action import ActionItemCreate, ActionItemUpdate, ActionItemResponse
from app.schemas.common import APIResponse
from app.services.action_service import action_service

router = APIRouter(prefix="/actions", tags=["Action Center"])


@router.get("", response_model=APIResponse[List[ActionItemResponse]])
def list_actions(
    incident_id: Optional[int] = Query(None, description="Filter by incident ID"),
    status: Optional[str] = Query(None, description="Filter by action status"),
    db: Session = Depends(get_db)
):
    """List response actions and task dispatches."""
    actions = action_service.get_actions(db, incident_id=incident_id, status=status)
    return APIResponse(
        success=True,
        message="Actions retrieved successfully",
        data=[ActionItemResponse.model_validate(a) for a in actions]
    )


@router.post("", response_model=APIResponse[ActionItemResponse])
def create_action(
    payload: ActionItemCreate,
    db: Session = Depends(get_db)
):
    """Dispatch a new municipal/police response action for an incident."""
    action = action_service.create_action(db, payload)
    return APIResponse(
        success=True,
        message=f"Action '{action.action_code}' dispatched to {action.assigned_team}",
        data=ActionItemResponse.model_validate(action)
    )


@router.patch("/{action_id}", response_model=APIResponse[ActionItemResponse])
def update_action(
    payload: ActionItemUpdate,
    action_id: int = Path(..., description="Action ID"),
    db: Session = Depends(get_db)
):
    """Update action status, priority, assigned team, or resolution notes."""
    action = action_service.update_action(db, action_id, payload)
    return APIResponse(
        success=True,
        message=f"Action '{action.action_code}' updated successfully",
        data=ActionItemResponse.model_validate(action)
    )


@router.get("/incident/{incident_id}", response_model=APIResponse[List[ActionItemResponse]])
def get_actions_for_incident(
    incident_id: int = Path(..., description="Incident ID"),
    db: Session = Depends(get_db)
):
    """Retrieve all actions assigned for a specific incident."""
    actions = action_service.get_actions(db, incident_id=incident_id)
    return APIResponse(
        success=True,
        message="Incident actions retrieved successfully",
        data=[ActionItemResponse.model_validate(a) for a in actions]
    )
