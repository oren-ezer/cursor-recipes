from datetime import datetime
from typing import Optional, List, Dict
from sqlmodel import SQLModel, Field
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import BaseModel
from sqlalchemy import UniqueConstraint

class Recipe(BaseModel):
    __tablename__ = "recipes"

    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=False)
    title: str = Field(nullable=False)
    description: Optional[str] = Field(default=None)
    ingredients: List[Dict[str, str]] = Field(nullable=False)
    instructions: List[str] = Field(nullable=False)
    preparation_time: int = Field(nullable=False)
    cooking_time: int = Field(nullable=False)
    servings: int = Field(nullable=False)
    user_id: str = Field(foreign_key="users.uuid", nullable=False)

    __table_args__ = (
        UniqueConstraint('uuid', name='unique_recipe_uuid'),
    ) 