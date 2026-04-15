"""Pluggable image storage abstraction with database, filesystem, and S3 backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import uuid
import logging

from sqlmodel import Session, select

from src.models.recipe_image import RecipeImage

logger = logging.getLogger(__name__)


@dataclass
class StoredImage:
    """Result of storing an image, returned by all backends."""
    image_id: str
    storage_ref: str
    storage_backend: str


class ImageStorageBackend(ABC):
    """Abstract base for image storage backends."""

    @abstractmethod
    def store(self, file_bytes: bytes, filename: str, content_type: str) -> StoredImage:
        ...

    @abstractmethod
    def retrieve(self, image_id: str) -> Tuple[bytes, str]:
        """Return (file_bytes, content_type). Raises ValueError if not found."""
        ...

    @abstractmethod
    def delete(self, image_id: str) -> None:
        ...

    @abstractmethod
    def get_serving_url(self, image_id: str) -> str:
        ...


class DatabaseStorage(ImageStorageBackend):
    """Stores image bytes in the recipe_images table (BYTEA column)."""

    def __init__(self, db: Session, api_prefix: str = "/api/v1"):
        self.db = db
        self.api_prefix = api_prefix.rstrip("/")

    def store(self, file_bytes: bytes, filename: str, content_type: str) -> StoredImage:
        image_uuid = str(uuid.uuid4())
        image = RecipeImage(
            uuid=image_uuid,
            filename=filename,
            content_type=content_type,
            size_bytes=len(file_bytes),
            storage_backend="database",
            storage_ref=image_uuid,
            data=file_bytes,
            is_primary=False,
        )
        self.db.add(image)
        self.db.flush()
        logger.info(f"Stored image {image_uuid} in database ({len(file_bytes)} bytes)")
        return StoredImage(
            image_id=image_uuid,
            storage_ref=image_uuid,
            storage_backend="database",
        )

    def retrieve(self, image_id: str) -> Tuple[bytes, str]:
        image = self.db.exec(
            select(RecipeImage).where(RecipeImage.uuid == image_id)
        ).first()
        if not image or image.data is None:
            raise ValueError(f"Image not found: {image_id}")
        return image.data, image.content_type

    def delete(self, image_id: str) -> None:
        image = self.db.exec(
            select(RecipeImage).where(RecipeImage.uuid == image_id)
        ).first()
        if image:
            self.db.delete(image)
            self.db.flush()

    def get_serving_url(self, image_id: str) -> str:
        return f"{self.api_prefix}/images/{image_id}"


class FileSystemStorage(ImageStorageBackend):
    """Stores image files on disk; metadata row in recipe_images (no BYTEA data)."""

    def __init__(self, db: Session, base_path: Path, api_prefix: str = "/api/v1"):
        self.db = db
        self.base_path = base_path
        self.api_prefix = api_prefix.rstrip("/")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def store(self, file_bytes: bytes, filename: str, content_type: str) -> StoredImage:
        image_uuid = str(uuid.uuid4())
        ext = Path(filename).suffix or ".bin"
        relative_path = f"{image_uuid}{ext}"
        file_path = self.base_path / relative_path

        file_path.write_bytes(file_bytes)

        image = RecipeImage(
            uuid=image_uuid,
            filename=filename,
            content_type=content_type,
            size_bytes=len(file_bytes),
            storage_backend="filesystem",
            storage_ref=relative_path,
            data=None,
            is_primary=False,
        )
        self.db.add(image)
        self.db.flush()
        logger.info(f"Stored image {image_uuid} on filesystem at {file_path}")
        return StoredImage(
            image_id=image_uuid,
            storage_ref=relative_path,
            storage_backend="filesystem",
        )

    def retrieve(self, image_id: str) -> Tuple[bytes, str]:
        image = self.db.exec(
            select(RecipeImage).where(RecipeImage.uuid == image_id)
        ).first()
        if not image or not image.storage_ref:
            raise ValueError(f"Image not found: {image_id}")
        file_path = self.base_path / image.storage_ref
        if not file_path.is_file():
            raise ValueError(f"Image file missing from disk: {file_path}")
        return file_path.read_bytes(), image.content_type

    def delete(self, image_id: str) -> None:
        image = self.db.exec(
            select(RecipeImage).where(RecipeImage.uuid == image_id)
        ).first()
        if image:
            if image.storage_ref:
                file_path = self.base_path / image.storage_ref
                file_path.unlink(missing_ok=True)
            self.db.delete(image)
            self.db.flush()

    def get_serving_url(self, image_id: str) -> str:
        return f"{self.api_prefix}/images/{image_id}"


class S3Storage(ImageStorageBackend):
    """Stub for future S3/MinIO/Supabase Storage integration."""

    def store(self, file_bytes: bytes, filename: str, content_type: str) -> StoredImage:
        raise NotImplementedError("S3 storage backend is not yet implemented")

    def retrieve(self, image_id: str) -> Tuple[bytes, str]:
        raise NotImplementedError("S3 storage backend is not yet implemented")

    def delete(self, image_id: str) -> None:
        raise NotImplementedError("S3 storage backend is not yet implemented")

    def get_serving_url(self, image_id: str) -> str:
        raise NotImplementedError("S3 storage backend is not yet implemented")


def create_storage_backend(db: Session, settings) -> ImageStorageBackend:
    """Factory: create the appropriate storage backend from settings."""
    backend = settings.IMAGE_STORAGE_BACKEND
    api_prefix = getattr(settings, "API_V1_STR", "/api/v1")
    if backend == "database":
        return DatabaseStorage(db=db, api_prefix=api_prefix)
    elif backend == "filesystem":
        return FileSystemStorage(
            db=db,
            base_path=Path(settings.IMAGE_STORAGE_PATH),
            api_prefix=api_prefix,
        )
    elif backend == "s3":
        return S3Storage()
    else:
        raise ValueError(f"Unknown storage backend: {backend}")
