"""Image upload and serving endpoints."""

from typing import Annotated, List
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
    is_primary: bool = False


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


def _require_recipe_owner(db: Session, recipe_id: int, user: dict) -> Recipe:
    recipe = db.exec(select(Recipe).where(Recipe.id == recipe_id)).first()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )
    is_owner = user.get("uuid") == recipe.user_id
    is_superuser = bool(user.get("is_superuser"))
    if not is_owner and not is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify images for this recipe",
        )
    return recipe


def _to_image_info(row: RecipeImage, storage: ImageStorageBackend) -> ImageInfo:
    return ImageInfo(
        image_id=row.uuid,
        serving_url=storage.get_serving_url(row.uuid),
        filename=row.filename,
        size_bytes=row.size_bytes,
        is_primary=row.is_primary,
    )


def _clear_primaries(db: Session, recipe_id: int) -> None:
    existing = db.exec(
        select(RecipeImage).where(
            RecipeImage.recipe_id == recipe_id,
            RecipeImage.is_primary == True,  # noqa: E712
        )
    ).all()
    for img in existing:
        img.is_primary = False
        db.add(img)


@router.post("/upload", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_images(
    http_request: Request,
    images: List[UploadFile] = File(..., description="Image files to upload"),
    recipe_id: int = Form(..., description="Recipe to associate images with"),
    storage: Annotated[ImageStorageBackend, Depends(get_image_storage)] = None,
    db: Annotated[Session, Depends(get_database_session)] = None,
):
    """Upload one or more images and associate them with a recipe."""
    user = _require_auth(http_request)
    recipe = _require_recipe_owner(db, recipe_id, user)

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

    has_primary = db.exec(
        select(RecipeImage).where(
            RecipeImage.recipe_id == recipe_id,
            RecipeImage.is_primary == True,  # noqa: E712
        )
    ).first() is not None

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

        stored = storage.store(
            file_bytes,
            upload.filename or "image",
            upload.content_type,
            recipe_id,
        )

        image_row = db.exec(
            select(RecipeImage).where(RecipeImage.uuid == stored.image_id)
        ).first()
        make_primary = not has_primary and idx == 0
        if image_row:
            if make_primary:
                image_row.is_primary = True
                has_primary = True
                recipe.image_url = storage.get_serving_url(stored.image_id)
                db.add(recipe)
            db.add(image_row)
            results.append(_to_image_info(image_row, storage))
        else:
            results.append(
                ImageInfo(
                    image_id=stored.image_id,
                    serving_url=storage.get_serving_url(stored.image_id),
                    filename=upload.filename or "image",
                    size_bytes=len(file_bytes),
                    is_primary=make_primary,
                )
            )

    db.commit()
    logger.info(f"Uploaded {len(results)} image(s) for recipe {recipe_id}")
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
        images=[_to_image_info(row, storage) for row in rows]
    )


@router.patch("/{image_uuid}/primary", response_model=ImageInfo)
async def set_primary_image(
    image_uuid: str,
    http_request: Request,
    storage: Annotated[ImageStorageBackend, Depends(get_image_storage)] = None,
    db: Annotated[Session, Depends(get_database_session)] = None,
):
    """Mark an image as the primary image for its recipe."""
    user = _require_auth(http_request)

    image_row = db.exec(
        select(RecipeImage).where(RecipeImage.uuid == image_uuid)
    ).first()
    if not image_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    recipe = _require_recipe_owner(db, image_row.recipe_id, user)
    _clear_primaries(db, image_row.recipe_id)
    image_row.is_primary = True
    db.add(image_row)
    recipe.image_url = storage.get_serving_url(image_row.uuid)
    db.add(recipe)
    db.commit()
    db.refresh(image_row)

    logger.info(f"Set image {image_uuid} as primary for recipe {image_row.recipe_id}")
    return _to_image_info(image_row, storage)


@router.delete("/{image_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_uuid: str,
    http_request: Request,
    storage: Annotated[ImageStorageBackend, Depends(get_image_storage)] = None,
    db: Annotated[Session, Depends(get_database_session)] = None,
):
    """Delete a stored image by its UUID."""
    user = _require_auth(http_request)

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
    _require_recipe_owner(db, recipe_id, user)

    storage.delete(image_uuid)
    db.flush()

    if was_primary:
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
