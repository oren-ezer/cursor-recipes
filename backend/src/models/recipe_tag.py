from typing import Optional
from sqlmodel import Field
from src.models.base import BaseModel

class RecipeTag(BaseModel, table=True):
    """
    RecipeTag model for the database.
    Represents the many-to-many relationship between recipes and tags.
    """
    __tablename__ = "recipe_tags"
    
    recipe_id: int = Field(foreign_key="recipes.id", primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", primary_key=True)

    def __repr__(self):
        return f"<RecipeTag recipe_id={self.recipe_id} tag_id={self.tag_id}>"

    def __str__(self):
        return f"<RecipeTag recipe_id={self.recipe_id} tag_id={self.tag_id}>"

    def __eq__(self, other):
        if not isinstance(other, RecipeTag):
            return False
        return self.recipe_id == other.recipe_id and self.tag_id == other.tag_id
