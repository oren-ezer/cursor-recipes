"""Image upload and serving endpoints."""

from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
import logging

from src.core.config import settings
from src.services.image_storage import ImageStorageBackend
from src.utils.dependencies import get_image_storage
from src.models.recipe_image import RecipeImage
from src.models.recipe import Recipe
from sqlmodel import Session, select
from src.utils.dependencies import get_database_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["images"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ImageInfo(BaseModel):
    image_id: str
    serving_url: str
    filename: str
    size_bytes: int


class ImageUploadResponse(BaseModel):
    images: List[ImageInfo]


def _require_auth(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


@router.post("/upload", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_images(
    http_request: Request,
    images: List[UploadFile] = File(..., description="Image files to upload"),
    recipe_id: Optional[int] = Form(None),
    storage: Annotated[ImageStorageBackend, Depends(get_image_storage)] = None,
    db: Annotated[Session, Depends(get_database_session)] = None,
):
    """Upload one or more images. Optionally associate them with a recipe."""
    _require_auth(http_request)

    if not images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one image is required",
        )
    if len(images) > settings.MAX_IMAGES_PER_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.MAX_IMAGES_PER_UPLOAD} images per upload",
        )

    max_bytes = settings.MAX_IMAGE_UPLOAD_SIZE_MB * 1024 * 1024
    results: List[ImageInfo] = []

    for idx, upload in enumerate(images):
        if upload.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{upload.filename}' has unsupported type '{upload.content_type}'. "
                       f"Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
            )

        file_bytes = await upload.read()
        if len(file_bytes) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{upload.filename}' exceeds {settings.MAX_IMAGE_UPLOAD_SIZE_MB} MB limit",
            )

        stored = storage.store(file_bytes, upload.filename or "image", upload.content_type)

        image_row = db.exec(
            select(RecipeImage).where(RecipeImage.uuid == stored.image_id)
        ).first()
        if image_row:
            if recipe_id is not None:
                image_row.recipe_id = recipe_id
            if idx == 0:
                image_row.is_primary = True
            db.add(image_row)

        results.append(
            ImageInfo(
                image_id=stored.image_id,
                serving_url=storage.get_serving_url(stored.image_id),
                filename=upload.filename or "image",
                size_bytes=len(file_bytes),
            )
        )

    if recipe_id is not None and results:
        recipe = db.exec(select(Recipe).where(Recipe.id == recipe_id)).first()
        if recipe:
            recipe.image_url = results[0].serving_url
            db.add(recipe)

    db.commit()
    logger.info(f"Uploaded {len(results)} image(s)")
    return ImageUploadResponse(images=results)


@router.get("/recipe/{recipe_id}", response_model=ImageUploadResponse)
async def get_recipe_images(
    recipe_id: int,
    storage: Annotated[ImageStorageBackend, Depends(get_image_storage)] = None,
    db: Annotated[Session, Depends(get_database_session)] = None,
):
    """Get all images associated with a recipe."""
    rows = db.exec(
        select(RecipeImage)
        .where(RecipeImage.recipe_id == recipe_id)
        .order_by(RecipeImage.is_primary.desc(), RecipeImage.created_at)
    ).all()
    return ImageUploadResponse(
        images=[
            ImageInfo(
                image_id=row.uuid,
                serving_url=storage.get_serving_url(row.uuid),
                filename=row.filename,
                size_bytes=row.size_bytes,
            )
            for row in rows
        ]
    )


@router.delete("/{image_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_uuid: str,
    http_request: Request,
    storage: Annotated[ImageStorageBackend, Depends(get_image_storage)] = None,
    db: Annotated[Session, Depends(get_database_session)] = None,
):
    """Delete a stored image by its UUID."""
    _require_auth(http_request)

    image_row = db.exec(
        select(RecipeImage).where(RecipeImage.uuid == image_uuid)
    ).first()
    if not image_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    recipe_id = image_row.recipe_id
    was_primary = image_row.is_primary

    storage.delete(image_uuid)
    db.flush()

    if recipe_id is not None and was_primary:
        next_image = db.exec(
            select(RecipeImage)
            .where(RecipeImage.recipe_id == recipe_id)
            .order_by(RecipeImage.created_at)
        ).first()
        recipe = db.exec(select(Recipe).where(Recipe.id == recipe_id)).first()
        if recipe:
            if next_image:
                next_image.is_primary = True
                db.add(next_image)
                recipe.image_url = storage.get_serving_url(next_image.uuid)
            else:
                recipe.image_url = None
            db.add(recipe)

    db.commit()
    logger.info(f"Deleted image {image_uuid}")


@router.get("/{image_uuid}")
async def get_image(
    image_uuid: str,
    storage: Annotated[ImageStorageBackend, Depends(get_image_storage)] = None,
):
    """Serve a stored image by its UUID."""
    try:
        data, content_type = storage.retrieve(image_uuid)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
