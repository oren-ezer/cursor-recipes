from datetime import datetime
from typing import Optional, List, Dict
from sqlmodel import SQLModel, Field
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import BaseModel
from sqlalchemy import Column, UniqueConstraint
from pydantic import field_validator, ConfigDict
from sqlalchemy.dialects.postgresql import JSON

class Recipe(BaseModel, table=True):
    """
    Recipe model for the database.
    Represents a cooking recipe with ingredients, instructions, and metadata.
    """
    model_config = ConfigDict(validate_assignment=True)
    __tablename__ = "recipes"

    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=False)
    title: str = Field(nullable=False)
    description: Optional[str] = Field(default=None)
    ingredients: List[Dict[str, str]] = Field(sa_column=Column(JSON, nullable=False))
    instructions: List[str] = Field(sa_column=Column(JSON, nullable=False))
    preparation_time: int = Field(nullable=False)
    cooking_time: int = Field(nullable=False)
    servings: int = Field(nullable=False)
    difficulty_level: str = Field(default="Easy", nullable=False)
    is_public: bool = Field(default=True, nullable=False)
    image_url: Optional[str] = Field(default=None)
    user_id: str = Field(foreign_key="users.uuid", nullable=False)

    __table_args__ = (
        UniqueConstraint('uuid', name='unique_recipe_uuid'),
    )

    def __repr__(self):
        return f"<Recipe title={self.title} description={self.description} uuid={self.uuid}>"

    def __str__(self):
        return f"<Recipe title={self.title}>"

    def __eq__(self, other):
        if not isinstance(other, Recipe):
            return False
        return self.title == other.title and self.user_id == other.user_id

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v:
            raise ValueError('Title cannot be empty')
        if len(v) < 3:
            raise ValueError('Title must be at least 3 characters long')
        return v

    @field_validator('ingredients')
    @classmethod
    def validate_ingredients(cls, v):
        if not v:
            raise ValueError('Ingredients list cannot be empty')
        for ingredient in v:
            if not isinstance(ingredient, dict):
                raise ValueError('Each ingredient must be a dictionary')
            if 'name' not in ingredient or 'amount' not in ingredient:
                raise ValueError('Each ingredient must have "name" and "amount" fields')
            if not ingredient['name'] or not ingredient['amount']:
                raise ValueError('Ingredient name and amount cannot be empty')
            if len(ingredient)!=2:
                raise ValueError('Ingredient must only have name and amount')
        return v

    @field_validator('instructions')
    @classmethod
    def validate_instructions(cls, v):
        if not v:
            raise ValueError('Instructions list cannot be empty')
        for instruction in v:
            if not isinstance(instruction, str):
                raise ValueError('Each instruction must be a string')
            if not instruction.strip():
                raise ValueError('Instruction cannot be empty or only whitespaces')
        return v

    @field_validator('preparation_time', 'cooking_time')
    @classmethod
    def validate_time(cls, v):
        if v <= 0:
            raise ValueError('Time must be positive')
        if v > 4320:  # 72 hours in minutes
            raise ValueError('Time cannot exceed 3 days (1440 minutes)')
        return v

    @field_validator('servings')
    @classmethod
    def validate_servings(cls, v):
        if v <= 0:
            raise ValueError('Servings must be positive')
        if v > 100:  # Reasonable maximum
            raise ValueError('Servings cannot exceed 100')
        return v

    @field_validator('difficulty_level')
    @classmethod
    def validate_difficulty_level(cls, v):
        valid_levels = ['Easy', 'Medium', 'Hard', 'Expert']
        if v not in valid_levels:
            raise ValueError(f'Difficulty level must be one of: {", ".join(valid_levels)}')
        return v 