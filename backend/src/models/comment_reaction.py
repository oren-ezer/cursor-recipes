from sqlmodel import Field
from sqlalchemy import UniqueConstraint
from src.models.base import BaseModel

class CommentReaction(BaseModel, table=True):
    """
    User reaction to a recipe comment.
    """
    __tablename__ = "comment_reactions"
    
    user_id: str = Field(foreign_key="users.uuid", nullable=False)
    comment_id: int = Field(foreign_key="recipe_comments.id", nullable=False, ondelete="CASCADE")
    reaction_type: str = Field(nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "comment_id", name="unique_comment_reaction"),
    )
