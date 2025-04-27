from typing import Optional
from sqlmodel import Field
from app.models.base import BaseModel

class User(BaseModel, table=True):
    """
    User model for the database.
    """
    __tablename__ = "users"
    
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False) 