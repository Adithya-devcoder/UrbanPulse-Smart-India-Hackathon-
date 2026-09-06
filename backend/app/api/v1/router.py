from fastapi import APIRouter
from app.api.v1.ai_ingestion import router as ai_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.roads import router as roads_router
from app.api.v1.cameras import router as cameras_router
from app.api.v1.vehicles import router as vehicles_router
from app.api.v1.heatmap import router as heatmap_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.actions import router as actions_router
from app.api.v1.search import router as search_router

api_v1_router = APIRouter()

api_v1_router.include_router(ai_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(incidents_router)
api_v1_router.include_router(roads_router)
api_v1_router.include_router(cameras_router)
api_v1_router.include_router(vehicles_router)
api_v1_router.include_router(heatmap_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(actions_router)
api_v1_router.include_router(search_router)
