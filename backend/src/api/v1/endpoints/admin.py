from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.config import settings
from src.utils.dependencies import get_database_session, get_tag_service
from src.services.tag_service import TagService
from pydantic import BaseModel
from datetime import datetime
from typing import Annotated
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admins", tags=["admins"])

@router.get("/config-test")
async def test_config():
    """
    Test endpoint to verify environment variables are loaded correctly.
    """
    return {
        "database_url_configured": bool(settings.DATABASE_URL),
        "database_url": settings.DATABASE_URL,
        "database_url_length": len(settings.DATABASE_URL) if settings.DATABASE_URL else 0,
        "supabase_url_configured": bool(settings.SUPABASE_URL),
        "supabase_url": settings.SUPABASE_URL,
        "supabase_key_configured": bool(settings.SUPABASE_KEY),
        "supabase_service_key_configured": bool(settings.SUPABASE_SERVICE_KEY),
        "supabase_url_length": len(settings.SUPABASE_URL) if settings.SUPABASE_URL else 0,
        "supabase_key_length": len(settings.SUPABASE_KEY) if settings.SUPABASE_KEY else 0,
        "supabase_service_key_length": len(settings.SUPABASE_SERVICE_KEY) if settings.SUPABASE_SERVICE_KEY else 0
    }

@router.get("/test-setup")
async def test_setup():
    """
    Test endpoint to verify SQLModel setup without database connection.
    """
    try:
        # Test that we can import and use SQLModel components
        from sqlmodel import SQLModel
        from src.models.user import User
        from src.models.recipe import Recipe
        
        return {
            "status": "success",
            "message": "SQLModel setup is working correctly",
            "details": {
                "sqlmodel_imported": True,
                "user_model_imported": True,
                "recipe_model_imported": True,
                "database_url_configured": bool(settings.DATABASE_URL),
                "database_url_length": len(settings.DATABASE_URL) if settings.DATABASE_URL else 0
            }
        }
    except Exception as e:
        logger.error(f"Setup test error: {str(e)}")
        return {
            "status": "error",
            "message": "SQLModel setup has issues",
            "error": str(e)
        }

@router.get("/test-db-connection")
async def test_db_connection(
    request: Request,
    db: Session = Depends(get_database_session)
):
    """
    Test if a database connection can be established using SQLModel/Session.
    """
    try:
        logger.info("Testing database connection...")
        
        # Simple connection test - just try to execute a basic query
        db.execute(text("SELECT 1"))
        
        return {
            "status": "success",
            "message": "Database connection established successfully",
            "connection_method": "SQLModel/Session"
        }
        
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return {
            "status": "error",
            "message": "Failed to establish database connection",
            "error": str(e),
            "error_type": type(e).__name__
        }

# Admin tag endpoints

class TagResponse(BaseModel):
    id: int
    uuid: str
    name: str
    recipe_counter: int
    category: str
    created_at: datetime
    updated_at: datetime

class TagCreate(BaseModel):
    name: str

class TagUpdate(BaseModel):
    name: str

@router.get("/tags/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: int,
    tag_service: Annotated[TagService, Depends(get_tag_service)]
):
    """
    Get a specific tag by ID (admin only).
    
    Args:
        tag_id: The ID of the tag to retrieve
        tag_service: TagService instance with database session
        
    Returns:
        Tag data
        
    Raises:
        HTTPException: If tag not found or there's an error retrieving it
    """
    try:
        tag = tag_service.get_tag(tag_id)
        
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with ID {tag_id} not found"
            )
        
        return tag
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tag {tag_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tag: {str(e)}"
        )

@router.get("/tags/uuid/{tag_uuid}", response_model=TagResponse)
async def get_tag_by_uuid(
    tag_uuid: str,
    tag_service: Annotated[TagService, Depends(get_tag_service)]
):
    """
    Get a specific tag by UUID (admin only).
    
    Args:
        tag_uuid: The UUID of the tag to retrieve
        tag_service: TagService instance with database session
        
    Returns:
        Tag data
        
    Raises:
        HTTPException: If tag not found or there's an error retrieving it
    """
    try:
        tag = tag_service.get_tag_by_uuid(tag_uuid)
        
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with UUID {tag_uuid} not found"
            )
        
        return tag
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tag by UUID {tag_uuid}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tag: {str(e)}"
        )

@router.get("/tags/name/{tag_name}", response_model=TagResponse)
async def get_tag_by_name(
    tag_name: str,
    tag_service: Annotated[TagService, Depends(get_tag_service)]
):
    """
    Get a specific tag by name (admin only).
    
    Args:
        tag_name: The name of the tag to retrieve
        tag_service: TagService instance with database session
        
    Returns:
        Tag data
        
    Raises:
        HTTPException: If tag not found or there's an error retrieving it
    """
    try:
        tag = tag_service.get_tag_by_name(tag_name)
        
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with name '{tag_name}' not found"
            )
        
        return tag
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tag by name {tag_name}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tag: {str(e)}"
        )

@router.post("/tags/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    tag_service: Annotated[TagService, Depends(get_tag_service)]
):
    """
    Create a new tag (admin only).
    
    Args:
        tag_data: The tag data to create
        tag_service: TagService instance with database session
        
    Returns:
        Created tag data
        
    Raises:
        HTTPException: If creation fails or tag name already exists
    """
    try:
        created_tag = tag_service.create_tag(tag_data.name)
        return created_tag
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating tag: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tag: {str(e)}"
        )

@router.put("/tags/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    tag_service: Annotated[TagService, Depends(get_tag_service)]
):
    """
    Update a tag by ID (admin only).
    
    Args:
        tag_id: The ID of the tag to update
        tag_data: The tag data to update
        tag_service: TagService instance with database session
        
    Returns:
        Updated tag data
        
    Raises:
        HTTPException: If tag not found, update fails, or name already exists
    """
    try:
        updated_tag = tag_service.update_tag(tag_id, tag_data.name)
        return updated_tag
        
    except ValueError as e:
        if "Tag not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating tag {tag_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tag: {str(e)}"
        )

@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    tag_service: Annotated[TagService, Depends(get_tag_service)]
):
    """
    Delete a tag by ID (admin only).
    
    Args:
        tag_id: The ID of the tag to delete
        tag_service: TagService instance with database session
        
    Returns:
        None (204 No Content)
        
    Raises:
        HTTPException: If tag not found, has associations, or deletion fails
    """
    try:
        tag_service.delete_tag(tag_id)
        return None  # 204 No Content
        
    except ValueError as e:
        if "Tag not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting tag {tag_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete tag: {str(e)}"
        )