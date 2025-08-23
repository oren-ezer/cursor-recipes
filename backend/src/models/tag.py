from typing import Optional
from sqlmodel import Field
from src.models.base import BaseModel
from pydantic import field_validator, ConfigDict
import re
import uuid
from enum import Enum

class TagCategory(str, Enum):
    """Tag categories enum"""
    MEAL_TYPES = "Meal Types"
    SPECIAL_DIETARY = "Special Dietary"
    COURSE_TYPES = "Course Types"
    CUISINE_TYPES = "Cuisine Types"
    MAIN_INGREDIENTS = "Main Ingredients"
    COOKING_METHODS = "Cooking Methods"
    SPECIAL_CATEGORIES = "Special Categories"

class Tag(BaseModel, table=True):
    """
    Tag model for the database.
    Represents a category or tag that can be applied to recipes.
    """
    model_config = ConfigDict(validate_assignment=True)
    __tablename__ = "tags"
    
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)
    name: str = Field(unique=True, index=True, nullable=False)
    recipe_counter: int = Field(default=0, nullable=False)
    category: str = Field(nullable=False)

    def __repr__(self):
        return f"<Tag name={self.name} id={self.id} recipe_counter={self.recipe_counter} category={self.category}>"

    def __str__(self):
        return f"<Tag name={self.name}>"

    def __eq__(self, other):
        if not isinstance(other, Tag):
            return False
        return self.name.lower() == other.name.lower()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """
        Validate tag name.
        
        Args:
            v: Tag name to validate
            
        Returns:
            The normalized tag name if valid
            
        Raises:
            ValueError: If tag name doesn't meet requirements
        """
        
        # Check if name is a string
        if not isinstance(v, str):
            raise ValueError('Tag name must be a string')
        
        # Check not empty
        if not v:
            raise ValueError('Tag name cannot be empty')
        
        # Check minimum length
        if len(v.strip()) < 2:
            raise ValueError('Tag name must be at least 2 characters long')
        
        # Check maximum length
        if len(v.strip()) > 50:
            raise ValueError('Tag name cannot exceed 50 characters')
        
        # Check for valid characters (letters, numbers, spaces, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v.strip()):
            raise ValueError('Tag name can only contain letters, numbers, spaces, hyphens, and underscores')
        
        # Normalize the name (trim whitespace and convert to lowercase)
        return v.strip().lower()

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        """
        Validate tag category.
        
        Args:
            v: Category value to validate
            
        Returns:
            The category value if valid
            
        Raises:
            ValueError: If category is not a valid TagCategory value
        """
        valid_categories = [cat.value for cat in TagCategory]
        if v not in valid_categories:
            raise ValueError(f'Category must be one of: {valid_categories}')
        return v

    @classmethod
    def normalize_name(cls, name: str) -> str:
        """
        Normalize tag name for consistent storage and comparison.
        Converts to lowercase and removes extra whitespace.
        
        Args:
            name: Tag name to normalize
            
        Returns:
            Normalized tag name
        """
        return name.lower().strip()
