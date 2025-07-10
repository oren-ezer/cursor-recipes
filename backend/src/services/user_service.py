from typing import Optional
from sqlalchemy.orm import Session
from sqlmodel import select
from sqlalchemy import or_, and_
from src.models.user import User
from src.core.security import hash_password, verify_password, create_access_token
from src.core.config import settings
from datetime import datetime, timezone, timedelta
import uuid


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
    
    def search_for_users(self, email: Optional[str] = None, full_name: Optional[str] = None, 
                        is_active: Optional[bool] = None, limit: int = 100, offset: int = 0) -> dict:
        """
        Search users based on criteria with pagination using SQLModel/Session.
        
        Args:
            email: Filter by partial email address (case-insensitive)
            full_name: Filter by partial full name (case-insensitive)
            is_active: Filter by active status
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            Dictionary with users, total count, limit, and offset
        """
        # Build base statement
        statement = select(User)
        count_statement = select(User)
        
        # Build filters
        filters = []
        
        if email:
            filters.append(User.email.ilike(f"%{email}%"))
        
        if full_name:
            filters.append(User.full_name.ilike(f"%{full_name}%"))
        
        if is_active is not None:
            filters.append(User.is_active == is_active)
        
        # Apply filters if any
        if filters:
            statement = statement.where(and_(*filters))
            count_statement = count_statement.where(and_(*filters))
        
        # Add pagination and ordering
        statement = statement.offset(offset).limit(limit).order_by(User.id)
        
        # Execute queries
        users = self.db.exec(statement).all()
        total = len(self.db.exec(count_statement).all())
        
        return {
            "users": users,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def get_current_user(self, user_uuid: str) -> Optional[User]:
        """
        Get current user information by UUID.
        
        Args:
            user_uuid: The user's UUID from authentication
            
        Returns:
            User object if found, None otherwise
        """
        statement = select(User).where(User.uuid == user_uuid)
        return self.db.exec(statement).first()
    
    def create_user(self, email: str, password: str, full_name: Optional[str] = None) -> User:
        """
        Create a new user with email uniqueness check and password hashing.
        
        Args:
            email: User's email address
            password: Plain text password (will be hashed)
            full_name: Optional full name
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If email already exists or validation fails
        """
        # Check if user already exists
        existing_user = self.db.exec(select(User).where(User.email == email)).first()
        if existing_user:
            raise ValueError("Email already registered")

        # Validate password
        User.validate_password(password)

        # Hash the password
        hashed_password = hash_password(password)
        
        # Create new user
        current_time_utc = datetime.now(timezone.utc)
        new_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            is_superuser=False,
            created_at=current_time_utc,
            updated_at=current_time_utc,
            uuid=str(uuid.uuid4())
        )
        
        # Add to database (commit will be handled by FastAPI's dependency system)
        self.db.add(new_user)
        self.db.flush()  # Flush to get database-generated values like ID
        self.db.refresh(new_user)  # Ensure object is up-to-date
        
        return new_user
    
    def update_user(self, user_id: int, update_data: dict) -> User:
        """
        Update a user's profile information.
        
        Args:
            user_id: The ID of the user to update
            update_data: Dictionary containing the fields to update
            
        Returns:
            Updated User object
            
        Raises:
            ValueError: If user not found, email already taken, or validation fails
        """
        # Check if user exists first
        existing_user = self.db.exec(select(User).where(User.id == user_id)).first()
        if not existing_user:
            raise ValueError("User not found")
        
        # Handle email uniqueness check
        if "email" in update_data:
            # Check if new email is already taken by another user
            email_check = self.db.exec(
                select(User).where(
                    and_(
                        User.email == update_data["email"],
                        User.id != user_id
                    )
                )
            ).first()
            if email_check:
                raise ValueError("Email already taken by another user")
        
        # Handle password hashing
        if "password" in update_data:
            # Validate password using the model's validator
            User.validate_password(update_data["password"])
            # Hash the password before storing
            update_data["hashed_password"] = hash_password(update_data["password"])
            # Remove the plain password from update data
            del update_data["password"]
        
        # Update timestamp
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update the user object with new values
        for field, value in update_data.items():
            if hasattr(existing_user, field):
                setattr(existing_user, field, value)
        
        # Flush to persist changes
        self.db.flush()
        self.db.refresh(existing_user)
        
        return existing_user 

    def delete_user(self, user_id: int) -> None:
        """
        Delete a user by their ID.
        
        Args:
            user_id: The ID of the user to delete
        
        Raises:
            ValueError: If user not found
        """
        # Check if user exists
        existing_user = self.db.exec(select(User).where(User.id == user_id)).first()
        if not existing_user:
            raise ValueError("User not found")
        
        # Delete the user
        self.db.delete(existing_user)
        self.db.flush()
        # No return value (None for 204 No Content) 

    def set_superuser_status(self, user_id: int, is_superuser: bool) -> User:
        """
        Set the is_superuser status for a user.
        
        Args:
            user_id: The ID of the user to update
            is_superuser: The superuser status to set
        
        Returns:
            Updated User object
        
        Raises:
            ValueError: If user not found
        """
        # Check if user exists
        existing_user = self.db.exec(select(User).where(User.id == user_id)).first()
        if not existing_user:
            raise ValueError("User not found")
        
        # Update the user's superuser status and updated_at timestamp
        existing_user.is_superuser = is_superuser
        existing_user.updated_at = datetime.now(timezone.utc)
        
        # Flush to persist changes
        self.db.flush()
        self.db.refresh(existing_user)
        
        return existing_user 

    def login_for_access_token(self, username: str, password: str) -> dict:
        """
        Authenticate user and create access token.
        
        Args:
            username: User's email address
            password: Plain text password
            
        Returns:
            Dictionary with access_token and token_type
            
        Raises:
            ValueError: If user not found, password incorrect, or user inactive
        """
        # 1. Get user from DB by email (username)
        user = self.db.exec(select(User).where(User.email == username)).first()
        
        # Check if user exists
        if not user:
            raise ValueError("Incorrect email or password")
        
        # 2. Verify password
        if not verify_password(password, user.hashed_password):
            raise ValueError("Incorrect email or password")
            
        # 3. Check if user is active
        if not user.is_active:
            raise ValueError("Inactive user")

        # 4. Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "uuid": user.uuid}, 
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"} 