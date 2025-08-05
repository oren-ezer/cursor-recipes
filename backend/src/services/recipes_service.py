from sqlmodel import select
from sqlalchemy.orm import Session
from src.models.recipe import Recipe
from datetime import datetime


class RecipeService:
    """Service class for recipe-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_recipe(self, recipe_id: int) -> Recipe | None:
        """
        Get a recipe by ID.
        
        Args:
            recipe_id: The ID of the recipe to retrieve
            
        Returns:
            Recipe object if found, None otherwise
        """
        statement = select(Recipe).where(Recipe.id == recipe_id)
        return self.db.execute(statement).scalars().first()
    
    def get_all_recipes(self, limit: int = 100, offset: int = 0, user_id: str = None) -> dict:
        """
        Get all recipes with pagination support using limit/offset.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            user_id: Optional user ID to filter recipes by user
            
        Returns:
            Dictionary with recipes, total count, limit, and offset
        """
        # Build base statement
        statement = select(Recipe)
        count_statement = select(Recipe)
        
        # Add user filter if provided
        if user_id:
            statement = statement.where(Recipe.user_id == user_id)
            count_statement = count_statement.where(Recipe.user_id == user_id)
        
        # Add pagination
        statement = statement.offset(offset).limit(limit)
        
        # Get recipes for current page
        recipes = self.db.execute(statement).scalars().all()
        
        # Get total count
        total = len(self.db.execute(count_statement).scalars().all())
        
        return {
            "recipes": recipes,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def create_recipe(self, recipe_data: dict, user_uuid: str) -> Recipe:
        """
        Create a new recipe.
        
        Args:
            recipe_data: Dictionary containing recipe data
            user_uuid: UUID of the user creating the recipe
            
        Returns:
            Created Recipe object
            
        Raises:
            ValueError: If validation fails
        """
        recipe_data["user_id"] = user_uuid
        recipe = Recipe(**recipe_data)
        self.db.add(recipe)
        self.db.flush()
        self.db.refresh(recipe)
        return recipe
    
    def update_recipe(self, recipe_id: int, update_data: dict, user_uuid: str) -> Recipe:
        """
        Update a recipe.
        
        Args:
            recipe_id: The ID of the recipe to update
            update_data: Dictionary containing the fields to update
            user_uuid: UUID of the user updating the recipe
            
        Returns:
            Updated Recipe object
            
        Raises:
            ValueError: If recipe not found or user not authorized
        """
        statement = select(Recipe).where(Recipe.id == recipe_id)
        recipe = self.db.execute(statement).scalars().first()
        
        if not recipe:
            raise ValueError(f"Recipe with ID {recipe_id} not found")
        
        if recipe.user_id != user_uuid:
            raise ValueError("Not authorized to update this recipe")
        
        if not update_data:
            return recipe
        
        # Handle ingredients conversion if needed
        if "ingredients" in update_data and update_data["ingredients"] is not None:
            if hasattr(update_data["ingredients"][0], 'model_dump'):
                update_data["ingredients"] = [ingredient.model_dump() for ingredient in update_data["ingredients"]]
        
        # Update fields
        for field, value in update_data.items():
            if value is not None and hasattr(recipe, field):
                setattr(recipe, field, value)
        
        # Update timestamp
        recipe.updated_at = datetime.now()
        
        self.db.flush()
        self.db.refresh(recipe)
        return recipe
    
    def delete_recipe(self, recipe_id: int, user_uuid: str) -> None:
        """
        Delete a recipe.
        
        Args:
            recipe_id: The ID of the recipe to delete
            user_uuid: UUID of the user deleting the recipe
            
        Raises:
            ValueError: If recipe not found or user not authorized
        """
        statement = select(Recipe).where(Recipe.id == recipe_id)
        recipe = self.db.execute(statement).scalars().first()
        
        if not recipe:
            raise ValueError(f"Recipe with ID {recipe_id} not found")
        
        if recipe.user_id != user_uuid:
            raise ValueError("Not authorized to delete this recipe")
        
        self.db.delete(recipe)
        self.db.flush() 