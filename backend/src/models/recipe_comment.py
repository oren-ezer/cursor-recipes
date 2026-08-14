from sqlmodel import Field
from src.models.base import BaseModel

class RecipeComment(BaseModel, table=True):
    """
    User comment on a recipe.
    """
    __tablename__ = "recipe_comments"
    
    user_id: str = Field(foreign_key="users.uuid", nullable=False)
    recipe_id: int = Field(foreign_key="recipes.id", nullable=False, ondelete="CASCADE")
    content: str = Field(nullable=False)
