import json
from typing import Optional
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ai_ingestion import AIDetectionIngestRequest, AIDetectionIngestResponse
from app.schemas.common import APIResponse
from app.services.ai_ingestion_service import ai_ingestion_service
from app.core.errors import ValidationAppException

router = APIRouter(prefix="/ai", tags=["AI Ingestion"])


@router.post("/detections", response_model=APIResponse[AIDetectionIngestResponse])
async def ingest_ai_detection(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Unified Ingestion API for all 5 AI modules:
    1. Pothole / Road Defect Detection
    2. Damaged / Missing Traffic Sign Detection
    3. Vehicle Density & Classification
    4. Traffic Bottleneck Detection
    5. Vulnerable Pedestrian Situation
    
    Accepts:
    - application/json: Direct JSON payload (AIDetectionIngestRequest)
    - multipart/form-data: 'data' (JSON stringified metadata) + optional 'image' (camera frame file)
    """
    content_type = request.headers.get("content-type", "").lower()

    image_file: Optional[UploadFile] = None
    
    if "application/json" in content_type:
        try:
            body_bytes = await request.body()
            if not body_bytes:
                raise ValidationAppException("Request body cannot be empty")
            json_dict = json.loads(body_bytes.decode("utf-8"))
            req = AIDetectionIngestRequest(**json_dict)
        except Exception as e:
            if isinstance(e, ValidationAppException):
                raise e
            raise ValidationAppException(f"Invalid JSON payload: {str(e)}")
            
    elif "multipart/form-data" in content_type:
        form = await request.form()
        data_field = form.get("data")
        image_field = form.get("image")

        if not data_field:
            raise ValidationAppException("Multipart form-data must include 'data' field with JSON detection metadata")

        try:
            if isinstance(data_field, str):
                parsed = json.loads(data_field)
            else:
                parsed = json.loads(await data_field.read())
            req = AIDetectionIngestRequest(**parsed)
        except Exception as e:
            raise ValidationAppException(f"Invalid JSON metadata in 'data' field: {str(e)}")

        if image_field and hasattr(image_field, "filename"):
            image_file = image_field
    else:
        # Fallback attempt to parse JSON
        try:
            json_dict = await request.json()
            req = AIDetectionIngestRequest(**json_dict)
        except Exception as e:
            raise ValidationAppException(f"Unsupported content-type or malformed payload: {str(e)}")

    result = await ai_ingestion_service.process_detection(
        db=db,
        req=req,
        image_file=image_file
    )

    return APIResponse(
        success=True,
        message=result.message,
        data=result
    )
