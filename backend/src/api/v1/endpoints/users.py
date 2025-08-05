from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from src.utils.dependencies import get_user_service
from src.services.user_service import UserService
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Annotated
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

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
    email: Optional[str] = Query(None, description="Filter by partial email address (case-insensitive)"),
    full_name: Optional[str] = Query(None, description="Filter by partial full name (case-insensitive)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Search users based on criteria with pagination using limit/offset.
    """
    try:
        # Get users from service with search criteria
        result = user_service.search_for_users(
            email=email,
            full_name=full_name,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search users: {str(e)}"
        )

@router.get("/", response_model=UsersResponse)
async def get_users(
    user_service: Annotated[UserService, Depends(get_user_service)],
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Get all users with pagination using limit/offset.
    
    Args:
        limit: Maximum number of records to return (1-1000)
        offset: Number of records to skip
        user_service: UserService instance with database session
        
    Returns:
        List of users with pagination info
        
    Raises:
        HTTPException: If there's an error retrieving users
    """
    try:
        # Get users from service with pagination
        result = user_service.get_all_users(limit=limit, offset=offset)
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
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
        logger.info(f"===============================Request state: {request.state}")
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
async def get_user(user_id: int, user_service: Annotated[UserService, Depends(get_user_service)]):
    """
    Get user information by ID.
    
    Args:
        user_id: The ID of the user to retrieve
        user_service: UserService instance with database session
        
    Returns:
        User information (excluding password)
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user = user_service.get_user(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return user
        
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}"
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
            detail=f"Failed to register user: {str(e)}"
        )

@router.put("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    """
    Update a user's profile information.
    
    Args:
        user_id: The ID of the user to update
        user_data: The user data to update
        user_service: UserService instance with database session
        
    Returns:
        Updated user data (excluding password)
        
    Raises:
        HTTPException: If user not found or update fails
    """
    try:
        # Prepare update data, excluding None values from the input
        update_data = user_data.model_dump(exclude_unset=True)
        
        # If no fields to update, get current user data
        if not update_data:
            user = user_service.get_user(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return user
        
        # Update user via service
        updated_user = user_service.update_user(user_id, update_data)
        
        return updated_user
        
    except ValueError as e:
        # Handle business logic errors (e.g., user not found, email already taken)
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
    except Exception as e:
        logger.error(f"User update error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    """
    Delete a user by ID.
    """
    try:
        user_service.delete_user(user_id)
        return None  # 204 No Content
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
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )

@router.put("/{user_id}/set-superuser", response_model=UserResponse)
async def set_superuser_status(
    user_id: int, 
    payload: SetSuperuserRequest, 
    user_service: Annotated[UserService, Depends(get_user_service)]
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
    except Exception as e:
        logger.error(f"Error setting superuser status for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set superuser status: {str(e)}"
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


