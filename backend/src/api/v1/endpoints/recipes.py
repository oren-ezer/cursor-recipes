from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import List, Dict, Any, Optional, Annotated
from src.utils.db import Database
from src.utils.dependencies import get_recipe_service
from src.services.recipes_service import RecipeService
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recipes", tags=["recipes"])

class Ingredient(BaseModel):
    name: str
    amount: str

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
    user: str
    created_at: datetime
    updated_at: datetime
    is_public: bool
    image_url: Optional[str] = None

class RecipesResponse(BaseModel):
    recipes: List[RecipeResponse]
    total: int
    limit: int
    offset: int

@router.get("/", response_model=RecipesResponse)
async def read_recipes(
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service)],
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Get all recipes with pagination using limit/offset.
    
    Args:
        limit: Maximum number of records to return (1-1000)
        offset: Number of records to skip
        recipe_service: RecipeService instance with database session
        
    Returns:
        List of recipes with pagination info
        
    Raises:
        HTTPException: If there's an error retrieving recipes
    """
    try:
        # Get recipes from service with pagination
        result = recipe_service.get_all_recipes(limit=limit, offset=offset)
        
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
        logger.info(f"User from request state: {user}")
        
        if not user:
            logger.warning("No user found in request state")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        logger.info(f"Using user UUID: {user['uuid']}")
        
        # Get user's recipes from service with pagination
        result = recipe_service.get_all_recipes(limit=limit, offset=offset, user_id=user['uuid'])
        
        logger.info(f"Retrieved {len(result['recipes'])} recipes")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user recipes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recipes: {str(e)}"
        )

@router.get("/{recipe_id}", response_model=RecipeResponse)
async def read_recipe(
    recipe_id: int, 
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service)]
):
    """
    Get a specific recipe by ID.
    
    Args:
        recipe_id: The ID of the recipe to retrieve
        recipe_service: RecipeService instance with database session
        
    Returns:
        Recipe information
        
    Raises:
        HTTPException: If recipe not found
    """
    try:
        recipe = recipe_service.get_recipe(recipe_id)
        
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with ID {recipe_id} not found"
            )
            
        return recipe
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving recipe {recipe_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recipe: {str(e)}"
        )

@router.post("/")
async def create_recipe(recipe: Dict[str, Any]):
    """
    Create a new recipe.
    """
    try:
        new_recipe = Database.insert("recipes", recipe)
        return new_recipe
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating recipe: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recipe: {str(e)}"
        )

@router.put("/{recipe_id}")
async def update_recipe(recipe_id: int, recipe_data: Dict[str, Any], request: Request):
    """
    Update a recipe by ID.
    
    Args:
        recipe_id: The ID of the recipe to update
        recipe_data: The recipe data to update
        request: The request object (for accessing app state)
        
    Returns:
        Updated recipe data
        
    Raises:
        HTTPException: If recipe not found, user not authorized, or update fails
    """
    try:
        # Get user from request
        user = request.state.user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        # Check if recipe exists and belongs to user
        existing_recipes = Database.select("recipes", filters={"id": recipe_id})
        if not existing_recipes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with ID {recipe_id} not found"
            )
        
        existing_recipe = existing_recipes[0]
        if existing_recipe["user_id"] != user["uuid"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this recipe"
            )

        # Add updated timestamp
        recipe_data["updated_at"] = datetime.now().isoformat()
        
        # Update recipe
        updated_recipes = Database.update("recipes", recipe_data, {"id": recipe_id})
        if not updated_recipes:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update recipe"
            )
        
        return updated_recipes[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating recipe {recipe_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update recipe: {str(e)}"
        )

@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: int, request: Request):
    """
    Delete a recipe by ID.
    
    Args:
        recipe_id: The ID of the recipe to delete
        request: The request object (for accessing app state)
        
    Returns:
        None (204 No Content)
        
    Raises:
        HTTPException: If recipe not found, user not authorized, or deletion fails
    """
    try:
        # Get user from request
        user = request.state.user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        # Check if recipe exists and belongs to user
        existing_recipes = Database.select("recipes", filters={"id": recipe_id})
        if not existing_recipes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with ID {recipe_id} not found"
            )
        
        existing_recipe = existing_recipes[0]
        if existing_recipe["user_id"] != user["uuid"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this recipe"
            )

        # Delete recipe
        deleted_recipes = Database.delete("recipes", {"id": recipe_id})
        if not deleted_recipes:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete recipe"
            )
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting recipe {recipe_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete recipe: {str(e)}"
        ) 