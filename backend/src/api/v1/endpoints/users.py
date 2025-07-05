from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from src.core.config import settings
from src.core.security import hash_password, verify_password, create_access_token
from src.models.user import User
from src.utils.db import Database
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import logging
import socket
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
import uuid

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
    page: int
    page_size: int

class SetSuperuserRequest(BaseModel):
    is_superuser: bool

# New Token schema
class Token(BaseModel):
    access_token: str
    token_type: str

@router.get("/test-supabase")
async def test_supabase_connection(request: Request):
    """
    Test endpoint to verify Supabase connection from app state.
    """
    try:
        # Test connection by executing a simple query
        logger.info("Testing connection with a simple query...")
        users = Database.select("users", limit=1)
        
        return {
            "status": "success",
            "message": "Successfully connected to Supabase via Database utility",
            "data": users
        }
    except Exception as e:
        logger.error(f"Supabase connection error: {str(e)}")
        return {
            "status": "error",
            "message": "Failed to connect to Supabase",
            "error": str(e),
            "config": {
                "supabase_url": settings.SUPABASE_URL,
                "supabase_key_length": len(settings.SUPABASE_KEY) if settings.SUPABASE_KEY else 0,
                "supabase_service_key_length": len(settings.SUPABASE_SERVICE_KEY) if settings.SUPABASE_SERVICE_KEY else 0
            }
        }

@router.get("/config-test")
async def test_config():
    """
    Test endpoint to verify environment variables are loaded correctly.
    """
    return {
        "supabase_url_configured": bool(settings.SUPABASE_URL),
        "supabase_key_configured": bool(settings.SUPABASE_KEY),
        "supabase_service_key_configured": bool(settings.SUPABASE_SERVICE_KEY),
        "supabase_url_length": len(settings.SUPABASE_URL) if settings.SUPABASE_URL else 0,
        "supabase_key_length": len(settings.SUPABASE_KEY) if settings.SUPABASE_KEY else 0,
        "supabase_service_key_length": len(settings.SUPABASE_SERVICE_KEY) if settings.SUPABASE_SERVICE_KEY else 0
    }

@router.get("/test-db-connection", summary="Test Database Connection", description="Test the connection to the Supabase database")
async def test_db_connection(request: Request):
    """
    Test the connection to the Supabase database via Database utility.
    
    This endpoint attempts to connect to the Supabase database and perform a simple query.
    It returns detailed information about the connection status and any errors that occur.
    """
    try:
        # First, test DNS resolution
        supabase_url = settings.SUPABASE_URL
        parsed_url = urlparse(supabase_url)
        hostname = parsed_url.hostname
        
        logger.info(f"Testing DNS resolution for {hostname}...")
        try:
            ip_address = socket.gethostbyname(hostname)
            logger.info(f"Successfully resolved {hostname} to {ip_address}")
        except socket.gaierror as e:
            logger.error(f"DNS resolution failed for {hostname}: {str(e)}")
            return {
                "status": "error",
                "message": "Failed to resolve Supabase hostname",
                "error": str(e),
                "details": {
                    "hostname": hostname,
                    "error_type": "DNS_RESOLUTION_FAILED",
                    "error_message": str(e)
                }
            }
        
        # Test database connection via Database utility
        logger.info("Testing database connection via Database utility...")
        users = Database.select("users", limit=1)
        
        return {
            "status": "success",
            "message": "Successfully connected to the database via Database utility",
            "details": {
                "connection": "established",
                "query": "executed successfully",
                "response": users,
                "dns_resolution": {
                    "hostname": hostname,
                    "ip_address": ip_address
                }
            }
        }
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return {
            "status": "error",
            "message": "Failed to connect to the database",
            "error": str(e),
            "details": {
                "connection": "failed",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "supabase_url": settings.SUPABASE_URL,
                "supabase_key_length": len(settings.SUPABASE_KEY) if settings.SUPABASE_KEY else 0
            }
        }

@router.get("/search", response_model=UsersResponse)
async def search_users(
    request: Request,
    email: Optional[str] = Query(None, description="Filter by partial email address (case-insensitive)"),
    full_name: Optional[str] = Query(None, description="Filter by partial full name (case-insensitive)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """
    Search users based on criteria with pagination.
    """
    try:
        # Prepare filters
        ilike_filters = {}
        filters = {}
        
        if email:
            ilike_filters["email"] = email
        if full_name:
            ilike_filters["full_name"] = full_name
        if is_active is not None:
            filters["is_active"] = is_active
        
        result = Database.select_with_ilike(
            table="users",
            ilike_filters=ilike_filters if ilike_filters else None,
            filters=filters if filters else None,
            page=page,
            page_size=page_size,
            order_by="id"
        )
        
        return {
            "users": result["data"],
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search users: {str(e)}"
        )

@router.get("/", response_model=UsersResponse)
async def get_users(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """
    Get all users with pagination.
    
    Args:
        request: The request object (for accessing app state)
        page: Page number (starts from 1)
        page_size: Number of items per page (1-100)
        
    Returns:
        List of users with pagination info
        
    Raises:
        HTTPException: If there's an error retrieving users
    """
    try:
        result = Database.select_paginated(
            table="users",
            page=page,
            page_size=page_size,
            order_by="id"
        )
        
        return {
            "users": result["data"],
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(request: Request):
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
        
        # Get full user details from database
        user_data = Database.select_single("users", filters={"uuid": user["uuid"]})
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving current user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, request: Request):
    """
    Get user information by ID.
    
    Args:
        user_id: The ID of the user to retrieve
        request: The request object (for accessing app state)
        
    Returns:
        User information (excluding password)
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user = Database.select_single("users", filters={"id": user_id})
        
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
            detail=f"Failed to retrieve user: {str(e)}"
        )

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register_user(user_data: UserCreate, request: Request):
    """
    Register a new user.
    
    Args:
        user_data: User registration data including email, password, and optional full name
        request: The request object (for accessing app state)
        
    Returns:
        Created user data (excluding password)
        
    Raises:
        HTTPException: If email already exists or registration fails
    """
    try:
        # Check if user already exists
        existing_user = Database.select_single_tolerant("users", filters={"email": user_data.email})
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
            
        # Create new user
        hashed_password = hash_password(user_data.password)
        current_time_utc = datetime.now(timezone.utc).isoformat()

        new_user = {
            "email": user_data.email,
            "hashed_password": hashed_password,
            "full_name": user_data.full_name,
            "is_active": True,
            "is_superuser": False,
            "created_at": current_time_utc,
            "updated_at": current_time_utc,
            "uuid": str(uuid.uuid4())
        }
        
        # Insert user into database
        created_user = Database.insert_with_returning("users", new_user)
        
        if not created_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
            
        # Return created user (excluding password)
        return created_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )

@router.put("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate, request: Request):
    """
    Update a user's profile information.
    
    Args:
        user_id: The ID of the user to update
        user_data: The user data to update
        request: The request object (for accessing app state)
        
    Returns:
        Updated user data (excluding password)
        
    Raises:
        HTTPException: If user not found or update fails
    """
    try:
        # Check if user exists first to give a 404 if not found
        existing_user = Database.select_single("users", filters={"id": user_id})
        if not existing_user:
             raise HTTPException(
                 status_code=status.HTTP_404_NOT_FOUND,
                 detail="User not found"
             )
            
        # Prepare update data, excluding None values from the input
        update_data = user_data.model_dump(exclude_unset=True)
        
        # Handle specific fields
        if "email" in update_data:
            # Check if new email is already taken by another user
            email_check = Database.select_with_exclusions(
                "users", 
                filters={"email": update_data["email"]},
                exclusions={"id": user_id}
            )
            if email_check:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken by another user"
                )
            
        if "password" in update_data:
            try:
                User.password_validation(update_data["password"])
                # Hash the password before storing
                update_data["hashed_password"] = hash_password(update_data["password"])
                # Remove the plain password from update data
                del update_data["password"]
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            
        # If there's anything to update, add the timestamp
        if update_data:
            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        else:
            # No fields to update, return current user data
            return existing_user
        
        # Update user
        updated_users = Database.update("users", update_data, {"id": user_id})
        if not updated_users:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
            
        # Return updated user
        return updated_users[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, request: Request):
    """
    Delete a user by ID.
    """
    try:
        # Check if user exists first
        existing_user = Database.select_single("users", filters={"id": user_id})
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete the user using admin client for privileged operations
        deleted_users = Database.delete("users", {"id": user_id})
        
        # Note: Delete operations might not return data even when successful
        # The fact that we didn't get an exception means the operation was successful
        
        return None  # Return None for 204 No Content status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )

@router.put("/{user_id}/set-superuser", response_model=UserResponse)
async def set_superuser_status(user_id: int, payload: SetSuperuserRequest, request: Request):
    """
    Set the is_superuser status for a user. Requires admin privileges.
    """
    try:
        # Check if user exists first
        existing_user = Database.select_single("users", filters={"id": user_id})
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update the user's superuser status and updated_at timestamp
        update_data = {
            "is_superuser": payload.is_superuser,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        updated_users = Database.update("users", update_data, {"id": user_id})
        if not updated_users:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update superuser status"
            )
            
        return updated_users[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting superuser status for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set superuser status: {str(e)}"
        )

# Login endpoint
@router.post("/token", response_model=Token, tags=["authentication"])
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # 1. Get user from DB by email (username)
        db_users = Database.select("users", filters={"email": form_data.username}, limit=1)
        
        # Check if user exists
        if not db_users:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        db_user_data = db_users[0]

        # 2. Verify password
        if not verify_password(form_data.password, db_user_data["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 3. Check if user is active (optional, but good practice)
        if not db_user_data.get("is_active", True):  # Default to True if not present for some reason
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Inactive user"
            )

        # 4. Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user_data["email"], "user_id": db_user_data["id"], "uuid": db_user_data["uuid"]}, 
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


