from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from src.utils.dependencies import get_user_service, get_current_user
from src.services.user_service import UserService
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Annotated, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Verify that the current user is a superuser (admin)."""
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )
    return current_user

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    uuid: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

class UsersResponse(BaseModel):
    users: List[UserResponse]
    total: int
    limit: int
    offset: int

class SetSuperuserRequest(BaseModel):
    is_superuser: bool

# New Token schema
class Token(BaseModel):
    access_token: str
    token_type: str

@router.get("/search", response_model=UsersResponse)
async def search_users(
    user_service: Annotated[UserService, Depends(get_user_service)],
    admin: Dict[str, Any] = Depends(get_admin_user),
    email: Optional[str] = Query(None, description="Filter by partial email address (case-insensitive)"),
    full_name: Optional[str] = Query(None, description="Filter by partial full name (case-insensitive)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Search users based on criteria with pagination using limit/offset.
    Requires admin access.
    """
    try:
        result = user_service.search_for_users(
            email=email,
            full_name=full_name,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search users"
        )

@router.get("/", response_model=UsersResponse)
async def get_users(
    user_service: Annotated[UserService, Depends(get_user_service)],
    admin: Dict[str, Any] = Depends(get_admin_user),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Get all users with pagination using limit/offset.
    Requires admin access.
    """
    try:
        result = user_service.get_all_users(limit=limit, offset=offset)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    request: Request,
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    """
    Get current user information.
    """
    try:
        logger.debug("Fetching current user from request state")
        # Get user from request state
        user = request.state.user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        # Get full user details from service
        user_data = user_service.get_current_user(user["uuid"])
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user_data
        
    except HTTPException:
        # Let HTTPExceptions pass through
        raise
    except Exception as e:
        logger.error(f"Error retrieving current user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    user_service: Annotated[UserService, Depends(get_user_service)],
    admin: Dict[str, Any] = Depends(get_admin_user)
):
    """
    Get user information by ID.
    Requires admin access.
    """
    try:
        user = user_service.get_user(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    """
    Register a new user.
    
    Args:
        user_data: User registration data including email, password, and optional full name
        user_service: UserService instance with database session
        
    Returns:
        Created user data (excluding password)
        
    Raises:
        HTTPException: If email already exists or registration fails
    """
    try:
        # Create user via service
        created_user = user_service.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        return created_user
        
    except ValueError as e:
        # Handle business logic errors (e.g., email already exists)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"User registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )

@router.put("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_data: UserUpdate,
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a user's profile information.
    Requires auth; only the user themselves or a superuser may update.
    """
    is_self = current_user["id"] == user_id
    is_admin = current_user.get("is_superuser", False)
    if not is_self and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )

    try:
        update_data = user_data.model_dump(exclude_unset=True)
        
        if not update_data:
            user = user_service.get_user(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return user
        
        updated_user = user_service.update_user(user_id, update_data)
        
        return updated_user
        
    except ValueError as e:
        if "User not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        elif "Email already taken" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken by another user"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Dict[str, Any] = Depends(get_current_user),
    transfer_to_admin_id: Optional[int] = Query(None, description="ID of admin user to transfer recipes to if user owns recipes")
):
    """
    Delete a user by ID. If user owns recipes, transfer_to_admin_id must be provided.
    Requires auth; only the user themselves or a superuser may delete.
    """
    is_self = current_user["id"] == user_id
    is_admin = current_user.get("is_superuser", False)
    if not is_self and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )

    try:
        user_service.delete_user(user_id, transfer_to_admin_id)
        return None
    except ValueError as e:
        error_msg = str(e)
        if "User not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        elif "User owns" in error_msg or "Invalid admin user" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

@router.put("/{user_id}/set-superuser", response_model=UserResponse)
async def set_superuser_status(
    user_id: int, 
    payload: SetSuperuserRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    admin: Dict[str, Any] = Depends(get_admin_user)
):
    """
    Set the is_superuser status for a user. Requires admin privileges.
    """
    try:
        updated_user = user_service.set_superuser_status(user_id, payload.is_superuser)
        return updated_user
    except ValueError as e:
        if "User not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting superuser status for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set superuser status"
        )

# Login endpoint
@router.post("/token", response_model=Token, tags=["authentication"])
async def login_for_access_token(
    user_service: Annotated[UserService, Depends(get_user_service)],
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticate user and return access token.
    """
    try:
        # Authenticate user and get token via service
        token_data = user_service.login_for_access_token(
            username=form_data.username,
            password=form_data.password
        )
        
        return token_data
        
    except ValueError as e:
        # Handle authentication errors
        if "Incorrect email or password" in str(e):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif "Inactive user" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


