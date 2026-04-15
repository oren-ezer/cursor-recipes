from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.config import settings
from src.utils.dependencies import get_database_session, get_tag_service, get_recipe_service_with_tags, get_current_user
from src.services.tag_service import TagService
from src.services.recipes_service import RecipeService
from src.models.tag import TagCategory
from src.utils.sanitization import sanitize_text, MAX_LENGTHS
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Annotated, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admins", tags=["admins"])


def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Verify that the current user is a superuser (admin)."""
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )
    return current_user


@router.get("/config-test")
async def test_config(admin: Dict[str, Any] = Depends(get_admin_user)):
    """
    Test endpoint to verify environment variables are loaded correctly.
    Returns only boolean flags — no secrets or connection strings.
    """
    return {
        "database_url_configured": bool(settings.DATABASE_URL),
        "supabase_url_configured": bool(settings.SUPABASE_URL),
        "supabase_key_configured": bool(settings.SUPABASE_KEY),
        "supabase_service_key_configured": bool(settings.SUPABASE_SERVICE_KEY),
    }

@router.get("/test-setup")
async def test_setup(admin: Dict[str, Any] = Depends(get_admin_user)):
    """
    Test endpoint to verify SQLModel setup without database connection.
    """
    try:
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
            }
        }
    except Exception as e:
        logger.error(f"Setup test error: {str(e)}")
        return {
            "status": "error",
            "message": "SQLModel setup has issues",
        }

@router.get("/test-db-connection")
async def test_db_connection(
    admin: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_database_session)
):
    """
    Test if a database connection can be established using SQLModel/Session.
    """
    try:
        logger.info("Testing database connection...")
        
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
        }

# Admin recipe endpoints

class Ingredient(BaseModel):
    name: str
    amount: str

class TagInfo(BaseModel):
    id: int
    name: str
    category: str

class RecipeResponse(BaseModel):
    id: int
    uuid: str
    title: str
    description: str
    ingredients: List[Ingredient]
    instructions: List[str]
    preparation_time: int
    cooking_time: int
    servings: int
    difficulty_level: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    is_public: bool
    image_url: str | None = None
    tags: List[TagInfo] = []

class RecipesResponse(BaseModel):
    recipes: List[RecipeResponse]
    total: int
    limit: int
    offset: int

@router.get("/recipes/", response_model=RecipesResponse)
async def get_all_recipes(
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service_with_tags)],
    admin: Dict[str, Any] = Depends(get_admin_user),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Get ALL recipes (public and private) for admin management.
    Requires superuser authentication.
    """
    try:
        result = recipe_service.get_all_recipes_with_tags(limit=limit, offset=offset)
        return result
    except Exception as e:
        logger.error(f"Error retrieving all recipes for admin: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recipes"
        )

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
    name: str = Field(..., min_length=2, max_length=MAX_LENGTHS["tag_name"])
    category: str

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return sanitize_text(v, max_length=MAX_LENGTHS["tag_name"])

class TagUpdate(BaseModel):
    name: str = Field(..., min_length=2, max_length=MAX_LENGTHS["tag_name"])
    category: str

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return sanitize_text(v, max_length=MAX_LENGTHS["tag_name"])

@router.get("/tags/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: int,
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    admin: Dict[str, Any] = Depends(get_admin_user)
):
    """Get a specific tag by ID (admin only)."""
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
            detail="Failed to retrieve tag"
        )

@router.get("/tags/uuid/{tag_uuid}", response_model=TagResponse)
async def get_tag_by_uuid(
    tag_uuid: str,
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    admin: Dict[str, Any] = Depends(get_admin_user)
):
    """Get a specific tag by UUID (admin only)."""
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
            detail="Failed to retrieve tag"
        )

@router.get("/tags/name/{tag_name}", response_model=TagResponse)
async def get_tag_by_name(
    tag_name: str,
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    admin: Dict[str, Any] = Depends(get_admin_user)
):
    """Get a specific tag by name (admin only)."""
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
            detail="Failed to retrieve tag"
        )

@router.post("/tags/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    admin: Dict[str, Any] = Depends(get_admin_user)
):
    """Create a new tag (admin only)."""
    try:
        # Convert string category to TagCategory enum
        try:
            category = TagCategory(tag_data.category)
        except ValueError:
            valid_categories = [cat.value for cat in TagCategory]
            raise ValueError(f"Invalid category. Must be one of: {valid_categories}")
        
        created_tag = tag_service.create_tag(tag_data.name, category)
        return created_tag
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating tag: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tag"
        )

@router.put("/tags/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    admin: Dict[str, Any] = Depends(get_admin_user)
):
    """Update a tag by ID (admin only)."""
    try:
        # Convert string category to TagCategory enum
        try:
            category = TagCategory(tag_data.category)
        except ValueError:
            valid_categories = [cat.value for cat in TagCategory]
            raise ValueError(f"Invalid category. Must be one of: {valid_categories}")
        
        updated_tag = tag_service.update_tag(tag_id, tag_data.name, category)
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
            detail="Failed to update tag"
        )

class TagDeleteResponse(BaseModel):
    tag_name: str
    recipes_affected: int

@router.delete("/tags/{tag_id}", response_model=TagDeleteResponse)
async def delete_tag(
    tag_id: int,
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    admin: Dict[str, Any] = Depends(get_admin_user)
):
    """Delete a tag by ID (admin only)."""
    try:
        result = tag_service.delete_tag(tag_id)
        return result
        
    except ValueError as e:
        if "Tag not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting tag {tag_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete tag"
        )