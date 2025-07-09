from sqlmodel import select
from src.models.recipe import Recipe
from src.utils.db import Database


class RecipeService:
    """Service class for recipe-related operations."""
    
    def __init__(self, db: Database):
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
        return self.db.exec(statement).first()
    
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
            statement = statement.where(Recipe.user == user_id)
            count_statement = count_statement.where(Recipe.user == user_id)
        
        # Add pagination
        statement = statement.offset(offset).limit(limit)
        
        # Get recipes for current page
        recipes = self.db.execute(statement).scalars().all()
        
        # Get total count
        total = self.db.execute(count_statement).scalars().count()
        
        return {
            "recipes": recipes,
            "total": total,
            "limit": limit,
            "offset": offset
        } 