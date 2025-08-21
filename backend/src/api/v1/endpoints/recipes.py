from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import List, Dict, Any, Optional, Annotated
from src.utils.dependencies import get_recipe_service, get_tag_service
from src.services.recipes_service import RecipeService
from src.services.tag_service import TagService
from src.models.tag import TagCategory
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recipes", tags=["recipes"])

class Ingredient(BaseModel):
    name: str
    amount: str

class TagInfo(BaseModel):
    id: int
    name: str
    category: str

class RecipeCreate(BaseModel):
    title: str
    description: Optional[str] = None
    ingredients: List[Ingredient]
    instructions: List[str]
    preparation_time: int
    cooking_time: int
    servings: int
    difficulty_level: str = "Easy"
    is_public: bool = True
    image_url: Optional[str] = None
    tag_ids: Optional[List[int]] = None

class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[Ingredient]] = None
    instructions: Optional[List[str]] = None
    preparation_time: Optional[int] = None
    cooking_time: Optional[int] = None
    servings: Optional[int] = None
    difficulty_level: Optional[str] = None
    is_public: Optional[bool] = None
    image_url: Optional[str] = None
    tag_ids: Optional[List[int]] = None

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
    image_url: Optional[str] = None
    tags: List[TagInfo] = []

class RecipesResponse(BaseModel):
    recipes: List[RecipeResponse]
    total: int
    limit: int
    offset: int

@router.get("/", response_model=RecipesResponse)
async def read_recipes(
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service)],
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Get all public recipes with pagination using limit/offset.
    
    Args:
        limit: Maximum number of records to return (1-1000)
        offset: Number of records to skip
        recipe_service: RecipeService instance with database session
        
    Returns:
        List of public recipes with pagination info
        
    Raises:
        HTTPException: If there's an error retrieving recipes
    """
    try:
        # Set tag_service in recipe_service for this operation
        recipe_service.tag_service = tag_service
        
        # Get only public recipes with tags from service with pagination
        result = recipe_service.get_all_public_recipes_with_tags(limit=limit, offset=offset)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving recipes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recipes: {str(e)}"
        )

@router.get("/my", response_model=RecipesResponse)
async def read_my_recipes(
    request: Request,
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service)],
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Get the current user's recipes with pagination using limit/offset.
    
    Args:
        request: The request object (for accessing app state)
        limit: Maximum number of records to return (1-100)
        offset: Number of records to skip
        recipe_service: RecipeService instance with database session
        
    Returns:
        List of user's recipes with pagination info
        
    Raises:
        HTTPException: If there's an error retrieving recipes or user is not authenticated
    """
    try:
        # Get user from request
        user = request.state.user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        # Set tag_service in recipe_service for this operation
        recipe_service.tag_service = tag_service
        
        # Get user's recipes with tags from service
        result = recipe_service.get_all_my_recipes_with_tags(
            limit=limit, 
            offset=offset, 
            user_id=user["uuid"]
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user recipes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user recipes: {str(e)}"
        )

@router.get("/{recipe_id}", response_model=RecipeResponse)
async def read_recipe(
    recipe_id: int, 
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service)],
    tag_service: Annotated[TagService, Depends(get_tag_service)]
):
    """
    Get a specific recipe by ID.
    
    Args:
        recipe_id: The ID of the recipe to retrieve
        recipe_service: RecipeService instance with database session
        
    Returns:
        Recipe data
        
    Raises:
        HTTPException: If recipe not found or there's an error retrieving it
    """
    try:
        # Set tag_service in recipe_service for this operation
        recipe_service.tag_service = tag_service
        
        recipe_with_tags = recipe_service.get_recipe_with_tags(recipe_id)
        
        if not recipe_with_tags:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with ID {recipe_id} not found"
            )
        
        return recipe_with_tags
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving recipe {recipe_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recipe: {str(e)}"
        )

@router.post("/", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    request: Request,
    recipe_data: RecipeCreate,
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service)],
    tag_service: Annotated[TagService, Depends(get_tag_service)]
):
    """
    Create a new recipe.
    
    Args:
        request: The request object (for accessing app state)
        recipe_data: The recipe data to create
        recipe_service: RecipeService instance with database session
        tag_service: TagService instance with database session
        
    Returns:
        Created recipe data
        
    Raises:
        HTTPException: If user not authenticated or creation fails
    """
    try:
        user = request.state.user
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        
        recipe_dict = recipe_data.model_dump()
        recipe_dict["ingredients"] = [ingredient.model_dump() for ingredient in recipe_data.ingredients]
        
        # Set tag_service in recipe_service for this operation
        recipe_service.tag_service = tag_service
        
        # Create recipe with tags
        recipe_with_tags = recipe_service.create_recipe_with_tags(recipe_dict, user["uuid"])
        return recipe_with_tags
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating recipe: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create recipe: {str(e)}")

@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: int,
    recipe_data: RecipeUpdate,
    request: Request,
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service)],
    tag_service: Annotated[TagService, Depends(get_tag_service)]
):
    """
    Update a recipe by ID.
    
    Args:
        recipe_id: The ID of the recipe to update
        recipe_data: The recipe data to update
        request: The request object (for accessing app state)
        recipe_service: RecipeService instance with database session
        
    Returns:
        Updated recipe data
        
    Raises:
        HTTPException: If recipe not found, user not authorized, or update fails
    """
    try:
        user = request.state.user
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        
        update_dict = recipe_data.model_dump(exclude_unset=True)
        
        # Set tag_service in recipe_service for this operation
        recipe_service.tag_service = tag_service
        
        # Update recipe with tags
        recipe_with_tags = recipe_service.update_recipe_with_tags(recipe_id, update_dict, user["uuid"])
        return recipe_with_tags
        
    except ValueError as e:
        if "Recipe with ID" in str(e) and "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "Not authorized" in str(e):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating recipe {recipe_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update recipe: {str(e)}")

@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    request: Request,
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service)],
    tag_service: Annotated[TagService, Depends(get_tag_service)]
):
    """
    Delete a recipe by ID.
    
    Args:
        recipe_id: The ID of the recipe to delete
        request: The request object (for accessing app state)
        recipe_service: RecipeService instance with database session
        
    Returns:
        None (204 No Content)
        
    Raises:
        HTTPException: If recipe not found, user not authorized, or deletion fails
    """
    try:
        user = request.state.user
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        
        # Set tag_service in recipe_service for this operation
        recipe_service.tag_service = tag_service
        
        recipe_service.delete_recipe_with_tags(recipe_id, user["uuid"])
        return None  # 204 No Content
        
    except ValueError as e:
        if "Recipe with ID" in str(e) and "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "Not authorized" in str(e):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting recipe {recipe_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete recipe: {str(e)}") 