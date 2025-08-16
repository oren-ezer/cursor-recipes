from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlmodel import Session as SQLModelSession
from src.core.config import settings
from src.utils.database_session import engine
from src.services.user_service import UserService
from src.services.recipes_service import RecipeService
from src.services.tag_service import TagService
from typing import Annotated

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/users/token")

# Database session dependency for FastAPI endpoints
def get_database_session() -> Session:
    """
    FastAPI dependency to get SQLModel/SQLAlchemy database session.
    
    This follows the SQLModel best practices for session management.
    Each request gets its own session, and it's automatically closed.
    
    Returns:
        Session: SQLAlchemy database session with automatic lifecycle management
        
    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_database_session)):
            # Use db session here
            pass
    """
    with SQLModelSession(engine) as session:
        yield session

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

def get_recipe_service(db: Annotated[Session, Depends(get_database_session)]) -> RecipeService:
    """
    FastAPI dependency to get RecipeService instance with database session.
    
    Args:
        db: Database session from FastAPI dependency
        
    Returns:
        RecipeService: RecipeService instance with database session
        
    Usage:
        @app.get("/recipes/{recipe_id}")
        def get_recipe(recipe_service: RecipeService = Depends(get_recipe_service)):
            # Use recipe_service here
            pass
    """
    return RecipeService(db)

def get_tag_service(db: Annotated[Session, Depends(get_database_session)]) -> TagService:
    """
    FastAPI dependency to get TagService instance with database session.
    
    Args:
        db: Database session from FastAPI dependency
        
    Returns:
        TagService: TagService instance with database session
        
    Usage:
        @app.get("/tags/{tag_id}")
        def get_tag(tag_service: TagService = Depends(get_tag_service)):
            # Use tag_service here
            pass
    """
    return TagService(db)
# this method is designed to be used by FastAPI during dependency injection.
# currently it is not being used.
async def get_current_user(
    user_service: Annotated[UserService, Depends(get_user_service)],
    token: str = Depends(oauth2_scheme)
):
    return await _get_current_user_from_token(user_service, token)

# this method is used by the middleware to get the current user from the token
async def _get_current_user_from_token(user_service: UserService, token: str):
    """
    Internal function to get current user from token string.
    Used by middleware and other internal functions.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Decoding JWT token...")
        
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        user_uuid: str = payload.get("uuid")
        
        if email is None or user_id is None or user_uuid is None:
            logger.error("Missing required claims in token")
            raise credentials_exception
            
        # Get user from database using SQLAlchemy
        logger.info("Looking up user in database...")
        user = user_service.get_current_user(user_uuid)
        
        if not user:
            logger.error("User not found in database")
            raise credentials_exception
        
        logger.info("User authentication successful")
            
        # Convert SQLModel object to dict for consistency
        return {
            "id": user.id,
            "uuid": user.uuid,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        
    except JWTError:
        raise credentials_exception 