import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        case_sensitive=True,
        extra="allow"
    )

    PROJECT_NAME: str = "URBANPULSE API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # ── Database ────────────────────────────────────────────────────────────
    # Supabase: set DATABASE_URL in .env to your Supabase PostgreSQL URI
    # Falls back to local SQLite if not set
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'urbanpulse.db'}"
    )

    # ── Supabase direct API (optional — for realtime/storage features) ───────
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None

    # ── CORS ────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # CRA / other
        "http://127.0.0.1:5173",
        "*"
    ]

    # ── Storage ─────────────────────────────────────────────────────────────
    STORAGE_DIR: Path = BASE_DIR / "storage"
    EVIDENCE_DIR: Path = BASE_DIR / "storage" / "evidence"
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024   # 15 MB
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".webp"]

    # ── AI & OCR Config ─────────────────────────────────────────────────────
    OCR_ENGINE: str = "auto"   # 'auto' | 'pytesseract' | 'easyocr' | 'mock'
    POTHOLE_CORRELATION_METERS: float = 25.0
    POTHOLE_CORRELATION_SECONDS: float = 300.0

    # ── YOLO bridge ─────────────────────────────────────────────────────────
    # run.py posts detections to /api/v1/ai/detections using this secret header
    YOLO_BRIDGE_SECRET: str = "urbanpulse-sih-secret"

    # ── Demo Data ───────────────────────────────────────────────────────────
    AUTO_SEED_DEMO_DATA: bool = True


settings = Settings()

# Ensure storage directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

