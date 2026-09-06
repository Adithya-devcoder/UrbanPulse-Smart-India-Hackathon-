from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.errors import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from app.db.base import Base
from app.db.session import engine, SessionLocal
import app.models  # Ensure all model tables are registered
from app.services.seed_service import seed_service
from app.api.health import router as health_router
from app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup: Create tables
    Base.metadata.create_all(bind=engine)
    
    # 2. Seed demo data if configured
    if settings.AUTO_SEED_DEMO_DATA:
        db = SessionLocal()
        try:
            seed_service.seed_demo_data(db)
        finally:
            db.close()
            
    yield
    # Shutdown logic if needed


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=(
        "UrbanPulse: AI-Powered Urban Road Intelligence Backend.\n\n"
        "Ingests mobile sensor data from bus-mounted cameras across 5 AI modules: "
        "Road Defects/Potholes, Traffic Signs, Vehicle Density, Bottlenecks, and Vulnerable Pedestrians. "
        "Correlates events, manages evidence dossiers, calculates road risk, coordinates action teams, and generates PDF incident reports."
    ),
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Mount Static Storage for Evidence Images
app.mount("/api/v1/static", StaticFiles(directory=str(settings.STORAGE_DIR)), name="static")

# Include Routers
app.include_router(health_router)
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    return {
        "project": "URBANPULSE - AI-Powered Urban Road Intelligence",
        "version": settings.PROJECT_VERSION,
        "docs": "/docs",
        "health": "/health",
        "api_v1": "/api/v1"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
