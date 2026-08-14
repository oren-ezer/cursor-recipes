from sqlmodel import Field
from sqlalchemy import UniqueConstraint
from src.models.base import BaseModel
from pydantic import conint

class RecipeRating(BaseModel, table=True):
    """
    User rating for a recipe (1-5).
    """
    __tablename__ = "recipe_ratings"
    
    user_id: str = Field(foreign_key="users.uuid", nullable=False)
    recipe_id: int = Field(foreign_key="recipes.id", nullable=False, ondelete="CASCADE")
    score: int = Field(nullable=False, ge=1, le=5)

    __table_args__ = (
        UniqueConstraint("user_id", "recipe_id", name="unique_recipe_rating"),
    )
