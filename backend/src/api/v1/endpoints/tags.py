from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import List, Dict, Any, Optional, Annotated
from src.utils.dependencies import get_tag_service, get_recipe_service_with_tags, get_current_user
from src.services.tag_service import TagService
from src.services.recipes_service import RecipeService
from src.models.tag import TagCategory
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tags", tags=["tags"])

class TagResponse(BaseModel):
    id: int
    uuid: str
    name: str
    recipe_counter: int
    category: str
    created_at: datetime
    updated_at: datetime

class TagsResponse(BaseModel):
    tags: List[TagResponse]
    total: int
    limit: int
    offset: int

class GroupedTagsResponse(BaseModel):
    tags: List[TagResponse]
    grouped_tags: Dict[str, List[TagResponse]]
    total: int
    limit: int
    offset: int

class PopularTagResponse(BaseModel):
    tag: TagResponse
    usage_count: int

class PopularTagsResponse(BaseModel):
    tags: List[PopularTagResponse]

class TagCreate(BaseModel):
    name: str
    category: TagCategory

class TagUpdate(BaseModel):
    name: str
    category: TagCategory

class TagAssociationRequest(BaseModel):
    tag_id: int



class TagUpdateRequest(BaseModel):
    add_tag_ids: Optional[List[int]] = None
    remove_tag_ids: Optional[List[int]] = None

class TagUpdateResponse(BaseModel):
    added_tags: List[TagResponse]
    removed_tags: List[TagResponse]
    current_tags: List[TagResponse]
    warnings: List[str]
    errors: List[str]

# User endpoints

@router.get("/", response_model=GroupedTagsResponse)
async def get_all_tags(
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Get all tags with pagination using limit/offset, including category grouping.
    
    Args:
        limit: Maximum number of records to return (1-1000)
        offset: Number of records to skip
        tag_service: TagService instance with database session
        
    Returns:
        List of tags with pagination info and grouped by category
        
    Raises:
        HTTPException: If there's an error retrieving tags
    """
    try:
        result = tag_service.get_tags_with_category_info(limit=limit, offset=offset)
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving tags: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tags"
        )

@router.get("/grouped", response_model=Dict[str, List[TagResponse]])
async def get_tags_grouped_by_category(
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Get all tags grouped by their categories.
    
    Args:
        limit: Maximum number of records to return (1-1000)
        offset: Number of records to skip
        tag_service: TagService instance with database session
        
    Returns:
        Dictionary with category names as keys and lists of tags as values
        
    Raises:
        HTTPException: If there's an error retrieving grouped tags
    """
    try:
        result = tag_service.get_tags_by_category(limit=limit, offset=offset)
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving grouped tags: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve grouped tags"
        )

@router.get("/search", response_model=TagsResponse)
async def search_tags(
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    name: Optional[str] = Query(None, description="Filter by partial tag name (case-insensitive)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Search tags based on criteria with pagination.
    
    Args:
        name: Filter by partial tag name (case-insensitive)
        limit: Maximum number of records to return (1-1000)
        offset: Number of records to skip
        tag_service: TagService instance with database session
        
    Returns:
        List of matching tags with pagination info
        
    Raises:
        HTTPException: If there's an error searching tags
    """
    try:
        result = tag_service.search_tags(name=name, limit=limit, offset=offset)
        return result
        
    except Exception as e:
        logger.error(f"Error searching tags: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search tags"
        )

@router.get("/popular", response_model=PopularTagsResponse)
async def get_popular_tags(
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    limit: int = Query(10, ge=1, le=100, description="Maximum number of popular tags to return")
):
    """
    Get the most popular tags based on usage count.
    
    Args:
        limit: Maximum number of popular tags to return (1-100)
        tag_service: TagService instance with database session
        
    Returns:
        List of popular tags with usage counts
        
    Raises:
        HTTPException: If there's an error retrieving popular tags
    """
    try:
        result = tag_service.get_popular_tags(limit=limit)
        return {"tags": result}
        
    except Exception as e:
        logger.error(f"Error retrieving popular tags: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve popular tags"
        )

@router.get("/recipes/{recipe_id}/tags", response_model=List[TagResponse])
async def get_tags_for_recipe(
    recipe_id: int,
    request: Request,
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service_with_tags)]
):
    """
    Get all tags associated with a specific recipe.
    Public recipes are visible to everyone; private recipes require owner or admin.
    """
    try:
        recipe = recipe_service.get_recipe(recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with ID {recipe_id} not found"
            )

        if not recipe.is_public:
            user = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required to view tags for this recipe"
                )
            is_owner = user["uuid"] == recipe.user_id
            is_superuser = user.get("is_superuser", False)
            if not is_owner and not is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view tags for this private recipe"
                )

        tags = tag_service.get_tags_for_recipe(recipe_id)
        return tags
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tags for recipe {recipe_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recipe tags"
        )







@router.put("/recipes/{recipe_id}/tags", response_model=TagUpdateResponse)
async def update_recipe_tags(
    recipe_id: int,
    tag_data: TagUpdateRequest,
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service_with_tags)],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update tags for a recipe by adding and/or removing tags in a single operation.
    Requires auth; only the recipe owner or a superuser may modify tags.
    """
    recipe = recipe_service.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with ID {recipe_id} not found"
        )

    is_owner = current_user["uuid"] == recipe.user_id
    is_superuser = current_user.get("is_superuser", False)
    if not is_owner and not is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify tags for this recipe"
        )

    try:
        result = tag_service.update_recipe_tags(
            recipe_id=recipe_id,
            add_tag_ids=tag_data.add_tag_ids,
            remove_tag_ids=tag_data.remove_tag_ids
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating tags for recipe {recipe_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update recipe tags"
        )


