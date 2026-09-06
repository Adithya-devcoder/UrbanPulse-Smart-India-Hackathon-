import os
import uuid
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
from app.core.config import settings
from app.core.errors import ValidationAppException


class BaseStorageProvider(ABC):
    @abstractmethod
    async def save_upload_file(self, file: UploadFile, subfolder: str = "evidence") -> Tuple[str, str]:
        """Saves an UploadFile and returns (file_path, file_url)"""
        pass

    @abstractmethod
    def save_bytes(self, data: bytes, extension: str = ".jpg", subfolder: str = "evidence") -> Tuple[str, str]:
        """Saves raw bytes and returns (file_path, file_url)"""
        pass

    @abstractmethod
    def get_full_path(self, relative_or_absolute_path: str) -> Path:
        """Resolves full local path for file"""
        pass


class LocalStorageProvider(BaseStorageProvider):
    def __init__(self):
        self.base_dir = settings.STORAGE_DIR
        self.evidence_dir = settings.EVIDENCE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def _validate_extension(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationAppException(
                f"Unsupported file extension '{ext}'. Allowed: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
            )
        return ext

    def _generate_filename(self, ext: str) -> str:
        return f"{uuid.uuid4().hex}{ext}"

    async def save_upload_file(self, file: UploadFile, subfolder: str = "evidence") -> Tuple[str, str]:
        ext = self._validate_extension(file.filename or "image.jpg")
        target_dir = self.base_dir / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = self._generate_filename(ext)
        dest_path = target_dir / filename

        # Read content and enforce size limits
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise ValidationAppException(
                f"File size exceeds limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
            )

        with open(dest_path, "wb") as f:
            f.write(content)

        relative_path = f"storage/{subfolder}/{filename}"
        file_url = f"/api/v1/static/{subfolder}/{filename}"
        return str(dest_path), file_url

    def save_bytes(self, data: bytes, extension: str = ".jpg", subfolder: str = "evidence") -> Tuple[str, str]:
        ext = self._validate_extension(f"sample{extension}")
        target_dir = self.base_dir / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = self._generate_filename(ext)
        dest_path = target_dir / filename

        with open(dest_path, "wb") as f:
            f.write(data)

        relative_path = f"storage/{subfolder}/{filename}"
        file_url = f"/api/v1/static/{subfolder}/{filename}"
        return str(dest_path), file_url

    def get_full_path(self, relative_or_absolute_path: str) -> Path:
        p = Path(relative_or_absolute_path)
        if p.is_absolute():
            return p
        return settings.BASE_DIR / relative_or_absolute_path


storage_provider = LocalStorageProvider()
