from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import List, Dict, Any, Optional
from src.utils.db import Database
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
    user_id: str
    created_at: datetime
    updated_at: datetime
    is_public: bool
    image_url: Optional[str] = None

class RecipesResponse(BaseModel):
    recipes: List[RecipeResponse]
    total: int
    page: int
    page_size: int

@router.get("/", response_model=RecipesResponse)
async def read_recipes(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """
    Get all recipes with pagination.
    
    Args:
        request: The request object (for accessing app state)
        page: Page number (starts from 1)
        page_size: Number of items per page (1-100)
        
    Returns:
        List of recipes with pagination info
        
    Raises:
        HTTPException: If there's an error retrieving recipes
    """
    try:
        result = Database.select_paginated(
            table="recipes",
            page=page,
            page_size=page_size,
            order_by="id"
        )
        
        return {
            "recipes": result["data"],
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"]
        }
        
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
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """
    Get the current user's recipes with pagination.
    
    Args:
        request: The request object (for accessing app state)
        page: Page number (starts from 1)
        page_size: Number of items per page (1-100)
        
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
        
        result = Database.select_paginated(
            table="recipes",
            page=page,
            page_size=page_size,
            filters={"user_id": user['uuid']},
            order_by="created_at.desc"
        )
        
        logger.info(f"Retrieved {len(result['data'])} recipes")
        
        return {
            "recipes": result["data"],
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user recipes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recipes: {str(e)}"
        )

@router.get("/{recipe_id}")
async def read_recipe(recipe_id: int):
    """
    Get a specific recipe by ID.
    """
    try:
        recipes = Database.select("recipes", filters={"id": recipe_id})
        if not recipes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with ID {recipe_id} not found"
            )
        return recipes[0]
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