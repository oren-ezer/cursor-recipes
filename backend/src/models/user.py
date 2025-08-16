from typing import Optional
from sqlmodel import Field
from src.models.base import BaseModel
from pydantic import EmailStr, field_validator
import uuid
from pydantic import ConfigDict
import re

class User(BaseModel, table=True):
    """
    User model for the database.
    """
    model_config = ConfigDict(validate_assignment=True)
    __tablename__ = "users"
    
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)

    def __repr__(self):
        return f"<User email={self.email} full_name={self.full_name} is_active={self.is_active} is_superuser={self.is_superuser} uuid={self.uuid}>"

    def __str__(self):
        return f"<User email={self.email}>"

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return self.email == other.email 

    @classmethod
    def validate_password(cls, password: str) -> str:
        """
        Validate a plain text password.
        
        Args:
            password: Plain text password to validate
            
        Returns:
            The password if valid
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        
        # Check if password is a string
        # Check not empty
        if not password:
            raise ValueError('Password cannot be empty')
        
        # Check minimum length
        if len(password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValueError('Password must contain at least one uppercase letter')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValueError('Password must contain at least one lowercase letter')
        
        # Check for at least one number
        if not re.search(r'\d', password):
            raise ValueError('Password must contain at least one number')
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError('Password must contain at least one special character')
        
        # Check for common passwords
        common_passwords = {'password123', 'password123!', 'admin123', 'qwerty123', '12345678'}
        if password.lower() in common_passwords:
            raise ValueError('Password is too common')
        
        return password
 
