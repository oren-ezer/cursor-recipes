from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import List, Dict, Any, Optional
from src.utils.db import Database
from src.core.supabase_client import get_supabase_client
from pydantic import BaseModel
from datetime import datetime
import logging

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
        supabase = request.app.state.supabase
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        count_response = supabase.from_('recipes').select('*', count='exact').execute()
        total = count_response.count if count_response.count is not None else 0
        
        # Get paginated recipes
        response = supabase.from_('recipes') \
            .select('*') \
            .range(offset, offset + page_size - 1) \
            .order('id', desc=False) \
            .execute()
        
        return {
            "recipes": response.data,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    except AttributeError as ae:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Supabase client not initialized."
        )
    except Exception as e:
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recipe: {str(e)}"
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

        supabase = request.app.state.supabase
        logger.info(f"Using user UUID: {user['uuid']}")
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        count_response = supabase.from_('recipes').select('*', count='exact').eq('user_id', user['uuid']).execute()
        total = count_response.count if count_response.count is not None else 0
        logger.info(f"Total recipes found: {total}")
        
        # Get paginated recipes
        response = supabase.from_('recipes') \
            .select('*') \
            .eq('user_id', user['uuid']) \
            .range(offset, offset + page_size - 1) \
            .order('created_at', desc=True) \
            .execute()
        
        logger.info(f"Retrieved {len(response.data)} recipes")
        
        return {
            "recipes": response.data,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    except AttributeError as ae:
        logger.error(f"Attribute error: {str(ae)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Supabase client not initialized."
        )
    except Exception as e:
        logger.error(f"Error retrieving recipes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recipes: {str(e)}"
        ) 