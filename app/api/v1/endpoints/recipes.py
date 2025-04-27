from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.utils.db import Database
from app.core.supabase_client import get_supabase_client

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.get("/")
async def read_recipes():
    """
    Get all recipes.
    """
    try:
        recipes = Database.select("recipes")
        return {"recipes": recipes}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recipes: {str(e)}"
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