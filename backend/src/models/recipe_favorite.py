from sqlmodel import Field
from sqlalchemy import UniqueConstraint
from src.models.base import BaseModel

class RecipeFavorite(BaseModel, table=True):
    """
    User favorite for a recipe.
    """
    __tablename__ = "recipe_favorites"
    
    user_id: str = Field(foreign_key="users.uuid", nullable=False)
    recipe_id: int = Field(foreign_key="recipes.id", nullable=False, ondelete="CASCADE")

    __table_args__ = (
        UniqueConstraint("user_id", "recipe_id", name="unique_recipe_favorite"),
    )
