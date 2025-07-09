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
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> dict:
        """
        Get all users with pagination support using limit/offset.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            Dictionary with users, total count, limit, and offset
        """
        # Get users for current page
        statement = select(User).offset(offset).limit(limit)
        users = self.db.exec(statement).all()
        
        # Get total count
        count_statement = select(User)
        total = len(self.db.exec(count_statement).all())
        
        return {
            "users": users,
            "total": total,
            "limit": limit,
            "offset": offset
        } 