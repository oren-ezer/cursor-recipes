from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from backend.core.config import settings
from backend.core.security import hash_password, verify_password, create_access_token
from backend.models.user import User
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
        # Get the Supabase client from app state
        logger.info("Attempting to get Supabase client from app state...")
        supabase = request.app.state.supabase
        
        # Execute a simple query to test the connection
        logger.info("Testing connection with a simple query...")
        # response = supabase.from_('test_dummy').select('*').limit(1).execute()
        response = supabase.from_('users').select('*').limit(1).execute()
        
        return {
            "status": "success",
            "message": "Successfully connected to Supabase via app state",
            "data": response.data
        }
    except AttributeError:
        logger.error("Supabase client not found in app state.")
        return {
            "status": "error",
            "message": "Supabase client not found in app state. Check startup logs.",
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
    Test the connection to the Supabase database via app state.
    
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
        
        # Get the Supabase client from app state
        logger.info("Testing database connection via app state...")
        supabase = request.app.state.supabase
        
        # Execute a simple query to test the connection
        logger.info("Testing connection with a simple query...")
        # response = supabase.from_('test_dummy').select('*').limit(1).execute()
        response = supabase.from_('users').select('*').limit(1).execute()
        
        return {
            "status": "success",
            "message": "Successfully connected to the database via app state",
            "details": {
                "connection": "established",
                "query": "executed successfully",
                "response": response.data,
                "dns_resolution": {
                    "hostname": hostname,
                    "ip_address": ip_address
                }
            }
        }
    except AttributeError:
        logger.error("Supabase client not found in app state.")
        return {
            "status": "error",
            "message": "Supabase client not found in app state. Check startup logs.",
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
        supabase = request.app.state.supabase
        
        # Start building the query
        query = supabase.from_('users').select('*', count='exact')
        
        # Apply filters
        if email:
            query = query.ilike('email', f'%{email}%')
        if full_name:
            query = query.ilike('full_name', f'%{full_name}%')
        if is_active is not None:
            query = query.eq('is_active', is_active)
            
        # Calculate offset for pagination
        offset = (page - 1) * page_size
        
        # Apply pagination and ordering
        query = query.range(offset, offset + page_size - 1).order('id', desc=False)
        
        # Execute query
        response = query.execute()
        
        total = response.count if response.count is not None else 0
        
        return {
            "users": response.data,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    except AttributeError as ae:
        logger.error(f"Supabase client not found in app state: {str(ae)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Supabase client not initialized."
        )
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
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
        supabase = request.app.state.supabase
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        count_response = supabase.from_('users').select('*', count='exact').execute()
        total = count_response.count if count_response.count is not None else 0
        
        # Get paginated users
        response = supabase.from_('users') \
            .select('*') \
            .range(offset, offset + page_size - 1) \
            .order('id', desc=False) \
            .execute()
        
        return {
            "users": response.data,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    except AttributeError as ae:
        logger.error(f"Supabase client not found in app state: {str(ae)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Supabase client not initialized."
        )
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
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
        supabase = request.app.state.supabase
        
        # Get user from database
        response = supabase.from_('users').select('*').eq('id', user_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return response.data[0]
        
    except AttributeError as ae:
        logger.error(f"Supabase client not found in app state: {str(ae)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Supabase client not initialized."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user: {str(e)}")
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
        supabase = request.app.state.supabase
        # Check if user already exists
        existing_user = supabase.from_('users').select('id').eq('email', user_data.email).execute()
        
        if existing_user.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
            
        # Create new user
        hashed_password = hash_password(user_data.password)
        current_time_utc = datetime.now(timezone.utc).isoformat()
        # current_time = datetime.utcnow().isoformat()

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
        # Specify returning="representation" to get the inserted record back
        response = supabase.from_('users').insert(new_user, returning="representation").execute()
        
        if not response.data:
            # Attempt to provide more specific error details if possible
            error_detail = "Failed to create user"
            if hasattr(response, 'error') and response.error:
                error_detail += f": {response.error.message}"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_detail
            )
            
        # Return created user (excluding password)
        # The response.data should contain the created user directly now
        return response.data[0]
        
    except AttributeError:
        logger.error("Supabase client not found in app state.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Supabase client not initialized."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration error: {str(e)}")
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
        supabase = request.app.state.supabase
        
        # Check if user exists first to give a 404 if not found
        existing_check = supabase.from_('users').select('id').eq('id', user_id).maybe_single().execute()
        if not existing_check.data:
             raise HTTPException(
                 status_code=status.HTTP_404_NOT_FOUND,
                 detail="User not found"
             )
            
        # Prepare update data, excluding None values from the input
        update_data = user_data.model_dump(exclude_unset=True)
        
        # Handle specific fields
        if "email" in update_data:
            # Check if new email is already taken by another user
            email_check = supabase.from_('users').select('id').eq('email', update_data["email"]).neq('id', user_id).execute()
            if email_check.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken by another user"
                )
            
        if "password" in update_data:
            try:
                User.password_validation(update_data["password"])
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            
        # If there's anything to update, add the timestamp
        if update_data:
            
            # update_data["updated_at"] = datetime.utcnow().isoformat()
            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
        else:
            # No fields to update, return current user data or 204? Let's return current data.
             get_response = supabase.from_('users').select('*').eq('id', user_id).single().execute()
             return get_response.data
        
        # Update user
        response = supabase.from_('users').update(update_data).eq('id', user_id).execute()
        
        if not response.data:
             # Attempt to provide more specific error details if possible
            error_detail = "Failed to update user"
            if hasattr(response, 'error') and response.error:
                error_detail += f": {response.error.message}"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_detail
            )
            
        # Return updated user
        return response.data[0]
        
    except AttributeError:
        logger.error("Supabase client not found in app state.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Supabase client not initialized."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update error: {str(e)}")
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
        # Using admin client for deletion might be safer depending on RLS
        supabase = request.app.state.supabase_admin 
        
        # Check if user exists first
        existing_check = supabase.from_('users').select('id').eq('id', user_id).maybe_single().execute()
        if not existing_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete the user
        response = supabase.from_('users').delete().eq('id', user_id).execute()
        
        # Check if deletion was successful (optional, delete often succeeds even if 0 rows affected)
        # if not response.data: # This might not be reliable for delete
        #     logger.warning(f"Attempted to delete user {user_id}, but response indicates no data changed.")

        return None # Return None for 204 No Content status

    except AttributeError:
        logger.error("Supabase admin client not found in app state.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Supabase admin client not initialized."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
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
        # Use admin client for this privileged operation
        supabase = request.app.state.supabase_admin
        
        # Check if user exists first
        existing_check = supabase.from_('users').select('id').eq('id', user_id).maybe_single().execute()
        if not existing_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update the user's superuser status and updated_at timestamp
        update_data = {
            "is_superuser": payload.is_superuser,
            # "updated_at": datetime.utcnow().isoformat()
            "updated_at": datetime.now(timezone.utc).isoformat()
            
        }
        
        response = supabase.from_('users').update(update_data).eq('id', user_id).execute()
        
        if not response.data:
            # Attempt to provide more specific error details if possible
            error_detail = "Failed to update superuser status"
            if hasattr(response, 'error') and response.error:
                error_detail += f": {response.error.message}"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_detail
            )
            
        return response.data[0]

    except AttributeError:
        logger.error("Supabase admin client not found in app state.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Supabase admin client not initialized."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting superuser status for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set superuser status: {str(e)}"
        )

@router.get("/me")
async def read_users_me(request: Request):
    # This endpoint needs proper authentication to get the current user
    # For now, just show it can access the state
    try:
        _ = request.app.state.supabase # Check if state is accessible
        return {"message": "Current user endpoint (Supabase client accessible)"}
    except AttributeError:
        return {"message": "Current user endpoint (Supabase client NOT accessible in state)"}

# Login endpoint
@router.post("/token", response_model=Token, tags=["authentication"])
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    supabase = request.app.state.supabase
    
    # 1. Get user from DB by email (username)
    user_query_response = supabase.from_("users").select("*").eq("email", form_data.username).maybe_single().execute()
    
    # Check the response itself before accessing .data
    if not user_query_response or not hasattr(user_query_response, 'data') or not user_query_response.data:
        # This handles cases where user is not found OR if the query execution itself had an issue
        # that resulted in a response without a 'data' attribute (like the observed 406).
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_user_data = user_query_response.data

    # 2. Verify password
    if not verify_password(form_data.password, db_user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Check if user is active (optional, but good practice)
    if not db_user_data.get("is_active", True): # Default to True if not present for some reason
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


