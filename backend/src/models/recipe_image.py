"""RecipeImage model for storing uploaded recipe images with pluggable backends."""

from typing import Optional
from sqlmodel import Field
from sqlalchemy import Column, LargeBinary, UniqueConstraint
from .base import BaseModel
import uuid


class RecipeImage(BaseModel, table=True):
    __tablename__ = "recipe_images"
    __table_args__ = (
        UniqueConstraint("uuid", name="unique_recipe_image_uuid"),
    )

    uuid: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
    )
    recipe_id: Optional[int] = Field(default=None, foreign_key="recipes.id")
    filename: str
    content_type: str
    size_bytes: int
    storage_backend: str  # "database", "filesystem", "s3"
    storage_ref: Optional[str] = Field(default=None)
    data: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    is_primary: bool = Field(default=False)
