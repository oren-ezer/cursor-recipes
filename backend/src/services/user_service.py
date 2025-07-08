from typing import Optional
from sqlalchemy.orm import Session
from sqlmodel import select
from src.models.user import User


class UserService:
    """
    Service layer for user-related business logic.
    
    This service handles all user operations and encapsulates
    the business logic for user management.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the user service with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_user(self, user_id: int) -> Optional[User]:
        """
        Get a user by their ID.
        
        Args:
            user_id: The user's ID
            
        Returns:
            User object if found, None otherwise
        """
        statement = select(User).where(User.id == user_id)
        return self.db.exec(statement).first() 