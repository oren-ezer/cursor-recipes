from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from src.core.config import settings
from src.core.supabase_client import get_supabase_client
from src.utils.database_session import get_db
from src.services.user_service import UserService
from typing import Annotated

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/users/token")

# Database session dependency for FastAPI endpoints
def get_database_session() -> Session:
    """
    FastAPI dependency to get SQLModel/SQLAlchemy database session.
    
    Returns:
        Session: SQLAlchemy database session with automatic lifecycle management
        
    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_database_session)):
            # Use db session here
            pass
    """
    return next(get_db())

def get_user_service(db: Annotated[Session, Depends(get_database_session)]) -> UserService:
    """
    FastAPI dependency to get UserService instance with database session.
    
    Args:
        db: Database session from FastAPI dependency
        
    Returns:
        UserService: UserService instance with database session
        
    Usage:
        @app.get("/users/{user_id}")
        def get_user(user_service: UserService = Depends(get_user_service)):
            # Use user_service here
            pass
    """
    return UserService(db)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        user_uuid: str = payload.get("uuid")
        
        if email is None or user_id is None or user_uuid is None:
            raise credentials_exception
            
        # Get user from database
        supabase = get_supabase_client()
        response = supabase.from_('users').select('*').eq('uuid', user_uuid).maybe_single().execute()
        
        if not response.data:
            raise credentials_exception
            
        return response.data
        
    except JWTError:
        raise credentials_exception 