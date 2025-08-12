import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
from src.services.recipes_service import RecipeService
from src.models.recipe import Recipe
from sqlmodel import select


class TestRecipeService:
    """Test cases for RecipeService."""
    
    def test_get_recipe_found(self):
        """Test getting a recipe that exists."""
        # Arrange
        mock_db = Mock()
        mock_recipe = Recipe(
            id=1,
            uuid="test-recipe-uuid",
            title="Test Recipe",
            description="A test recipe",
            ingredients=[{"name": "Flour", "amount": "1 cup"}],
            instructions=["Mix ingredients", "Bake at 350F"],
            preparation_time=15,
            cooking_time=30,
            servings=4,
            difficulty_level="Easy",
            is_public=True,
            image_url="https://example.com/image.jpg",
            user_id="test-user-uuid"
        )

        # Mock the database execution
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = mock_recipe
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute

        recipe_service = RecipeService(mock_db)

        # Act
        result = recipe_service.get_recipe(1)

        # Assert
        assert result == mock_recipe
        mock_db.execute.assert_called_once()
    
    def test_get_recipe_not_found(self):
        """Test getting a recipe that doesn't exist."""
        # Arrange
        mock_db = Mock()
        
        # Mock the database execution to return None
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act
        result = recipe_service.get_recipe(999)
        
        # Assert
        assert result is None
        mock_db.execute.assert_called_once()
    
    def test_recipe_service_initialization(self):
        """Test that RecipeService is properly initialized with database session."""
        # Arrange
        mock_db = Mock()
        
        # Act
        recipe_service = RecipeService(mock_db)
        
        # Assert
        assert recipe_service.db == mock_db
    
    def test_get_recipe_with_zero_id(self):
        """Test getting a recipe with ID 0 (edge case)."""
        # Arrange
        mock_db = Mock()
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act
        result = recipe_service.get_recipe(0)
        
        # Assert
        assert result is None
        mock_db.execute.assert_called_once()
    
    def test_get_recipe_with_negative_id(self):
        """Test getting a recipe with negative ID (edge case)."""
        # Arrange
        mock_db = Mock()
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act
        result = recipe_service.get_recipe(-1)
        
        # Assert
        assert result is None
        mock_db.execute.assert_called_once()
    
    def test_get_recipe_database_exception(self):
        """Test handling of database exceptions."""
        # Arrange
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Database connection error")
        
        recipe_service = RecipeService(mock_db)
        
        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            recipe_service.get_recipe(1)
    
    def test_get_all_my_recipes_empty_list(self):
        """Test getting all my recipes when no recipes exist."""
        # Arrange
        mock_db = Mock()
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act
        result = recipe_service.get_all_my_recipes()
        
        # Assert
        assert result["recipes"] == []
        assert result["total"] == 0
        assert result["limit"] == 100
        assert result["offset"] == 0
        assert mock_db.execute.call_count == 2  # One for recipes, one for count
    
    def test_get_all_my_recipes_with_pagination(self):
        """Test getting all my recipes with pagination parameters."""
        # Arrange
        mock_db = Mock()
        mock_recipes = [
            Recipe(id=1, uuid="uuid1", title="Recipe 1", description="First recipe", 
                   ingredients=[{"name": "Flour", "amount": "1 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=10, cooking_time=20, servings=2, difficulty_level="Easy", 
                   is_public=True, user_id="user1"),
            Recipe(id=2, uuid="uuid2", title="Recipe 2", description="Second recipe", 
                   ingredients=[{"name": "Sugar", "amount": "1/2 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=15, cooking_time=25, servings=4, difficulty_level="Medium", 
                   is_public=True, user_id="user2")
        ]
        
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.side_effect = [mock_recipes, mock_recipes]  # First for recipes, second for count
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act
        result = recipe_service.get_all_my_recipes(limit=5, offset=10)
        
        # Assert
        assert result["recipes"] == mock_recipes
        assert result["total"] == 2
        assert result["limit"] == 5
        assert result["offset"] == 10
        assert mock_db.execute.call_count == 2  # One for recipes, one for count
    
    def test_get_all_my_recipes_multiple_recipes(self):
        """Test getting all my recipes when multiple recipes exist."""
        # Arrange
        mock_db = Mock()
        mock_recipes = [
            Recipe(id=1, uuid="uuid1", title="Recipe 1", description="First recipe", 
                   ingredients=[{"name": "Flour", "amount": "1 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=10, cooking_time=20, servings=2, difficulty_level="Easy", 
                   is_public=True, user_id="user1"),
            Recipe(id=2, uuid="uuid2", title="Recipe 2", description="Second recipe", 
                   ingredients=[{"name": "Sugar", "amount": "1/2 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=15, cooking_time=25, servings=4, difficulty_level="Medium", 
                   is_public=True, user_id="user2"),
            Recipe(id=3, uuid="uuid3", title="Recipe 3", description="Third recipe", 
                   ingredients=[{"name": "Eggs", "amount": "2"}], instructions=["Mix ingredients"], 
                   preparation_time=20, cooking_time=30, servings=6, difficulty_level="Hard", 
                   is_public=False, user_id="user3")
        ]
        
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.side_effect = [mock_recipes, mock_recipes]  # First for recipes, second for count
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act
        result = recipe_service.get_all_my_recipes()
        
        # Assert
        assert result["recipes"] == mock_recipes
        assert result["total"] == 3
        assert len(result["recipes"]) == 3
        assert mock_db.execute.call_count == 2  # One for recipes, one for count
    
    def test_get_all_my_recipes_default_parameters(self):
        """Test getting all my recipes with default parameters."""
        # Arrange
        mock_db = Mock()
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act
        result = recipe_service.get_all_my_recipes()
        
        # Assert
        assert result["recipes"] == []
        assert result["total"] == 0
        assert result["limit"] == 100
        assert result["offset"] == 0
        assert mock_db.execute.call_count == 2  # One for recipes, one for count
        # Verify the calls were made correctly
        # First call should be for recipes with pagination
        first_call_args = mock_db.execute.call_args_list[0][0][0]
        first_call_str = str(first_call_args).lower()
        assert "limit" in first_call_str
        assert "offset" in first_call_str
        # Second call should be for count without pagination
        second_call_args = mock_db.execute.call_args_list[1][0][0]
        second_call_str = str(second_call_args).lower()
        assert "limit" not in second_call_str
        assert "offset" not in second_call_str
    
    def test_get_all_my_recipes_database_exception(self):
        """Test handling of database exceptions in get_all_my_recipes."""
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Database error")
        recipe_service = RecipeService(mock_db)
        with pytest.raises(Exception, match="Database error"):
            recipe_service.get_all_my_recipes()

    def test_get_all_my_recipes_verify_select_statement(self):
        """Test that the correct select statement is used in get_all_my_recipes."""
        mock_db = Mock()
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        recipe_service = RecipeService(mock_db)
        recipe_service.get_all_my_recipes(limit=10, offset=20)
        # Check first call (recipes with pagination)
        first_call_args = mock_db.execute.call_args_list[0][0][0]
        first_call_str = str(first_call_args).lower()
        assert "select" in first_call_str
        assert "limit" in first_call_str
        assert "offset" in first_call_str
        # Check second call (count without pagination)
        second_call_args = mock_db.execute.call_args_list[1][0][0]
        second_call_str = str(second_call_args).lower()
        assert "select" in second_call_str
        assert "limit" not in second_call_str
        assert "offset" not in second_call_str

    def test_get_all_my_recipes_large_limit(self):
        """Test get_all_my_recipes with a very large limit."""
        mock_db = Mock()
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        recipe_service = RecipeService(mock_db)
        recipe_service.get_all_my_recipes(limit=10000, offset=0)
        # Check first call (recipes with pagination)
        first_call_args = mock_db.execute.call_args_list[0][0][0]
        first_call_str = str(first_call_args).lower()
        assert "limit" in first_call_str
        assert "offset" in first_call_str

    def test_get_all_my_recipes_negative_offset(self):
        """Test get_all_my_recipes with negative offset values."""
        mock_db = Mock()
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        recipe_service = RecipeService(mock_db)
        recipe_service.get_all_my_recipes(limit=10, offset=0)
        # Check first call (recipes with pagination)
        first_call_args = mock_db.execute.call_args_list[0][0][0]
        first_call_str = str(first_call_args).lower()
        assert "limit" in first_call_str
        assert "offset" in first_call_str

    def test_get_all_my_recipes_varied_fields(self):
        """Test get_all_my_recipes returns recipes with varied field values."""
        mock_db = Mock()
        mock_recipes = [
            Recipe(id=1, uuid="uuid1", title="Recipe 1", description="First recipe",
                   ingredients=[{"name": "Flour", "amount": "1 cup"}], instructions=["Mix ingredients"],
                   preparation_time=10, cooking_time=20, servings=2, difficulty_level="Easy",
                   is_public=True, user_id="user1"),
            Recipe(id=2, uuid="uuid2", title="Recipe 2", description="",
                   ingredients=[{"name": "Sugar", "amount": "1/2 cup"}], instructions=["Mix ingredients"],
                   preparation_time=15, cooking_time=25, servings=4, difficulty_level="Medium",
                   is_public=False, user_id="user2"),
            Recipe(id=3, uuid="uuid3", title="Recipe 3", description=None,
                   ingredients=[{"name": "Eggs", "amount": "2"}], instructions=["Mix ingredients"],
                   preparation_time=20, cooking_time=30, servings=6, difficulty_level="Hard",
                   is_public=True, image_url="https://example.com/recipe3.jpg", user_id="user3"),
        ]
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.side_effect = [mock_recipes, mock_recipes]  # First for recipes, second for count
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        recipe_service = RecipeService(mock_db)
        result = recipe_service.get_all_my_recipes()
        assert result["total"] == 3
        assert len(result["recipes"]) == 3
        assert result["limit"] == 100
        assert result["offset"] == 0
        assert mock_db.execute.call_count == 2  # One for recipes, one for count 

    # Tests for get_all_public_recipes
    def test_get_all_public_recipes_empty_list(self):
        """Test getting all public recipes when no recipes exist."""
        # Arrange
        mock_db = Mock()
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act
        result = recipe_service.get_all_public_recipes()
        
        # Assert
        assert result["recipes"] == []
        assert result["total"] == 0
        assert result["limit"] == 100
        assert result["offset"] == 0
        assert mock_db.execute.call_count == 2  # One for recipes, one for count

    def test_get_all_public_recipes_with_pagination(self):
        """Test getting all public recipes with pagination parameters."""
        # Arrange
        mock_db = Mock()
        mock_recipes = [
            Recipe(id=1, uuid="uuid1", title="Recipe 1", description="First recipe", 
                   ingredients=[{"name": "Flour", "amount": "1 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=10, cooking_time=20, servings=2, difficulty_level="Easy", 
                   is_public=True, user_id="user1"),
            Recipe(id=2, uuid="uuid2", title="Recipe 2", description="Second recipe", 
                   ingredients=[{"name": "Sugar", "amount": "1/2 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=15, cooking_time=25, servings=4, difficulty_level="Medium", 
                   is_public=True, user_id="user2")
        ]
        
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.side_effect = [mock_recipes, mock_recipes]  # First for recipes, second for count
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act
        result = recipe_service.get_all_public_recipes(limit=5, offset=10)
        
        # Assert
        assert result["recipes"] == mock_recipes
        assert result["total"] == 2
        assert result["limit"] == 5
        assert result["offset"] == 10
        assert mock_db.execute.call_count == 2  # One for recipes, one for count

    def test_get_all_public_recipes_only_public(self):
        """Test that get_all_public_recipes only returns public recipes."""
        # Arrange
        mock_db = Mock()
        mock_recipes = [
            Recipe(id=1, uuid="uuid1", title="Public Recipe 1", description="First public recipe", 
                   ingredients=[{"name": "Flour", "amount": "1 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=10, cooking_time=20, servings=2, difficulty_level="Easy", 
                   is_public=True, user_id="user1"),
            Recipe(id=2, uuid="uuid2", title="Public Recipe 2", description="Second public recipe", 
                   ingredients=[{"name": "Sugar", "amount": "1/2 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=15, cooking_time=25, servings=4, difficulty_level="Medium", 
                   is_public=True, user_id="user2")
        ]
        
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.side_effect = [mock_recipes, mock_recipes]  # First for recipes, second for count
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act
        result = recipe_service.get_all_public_recipes()
        
        # Assert
        assert result["recipes"] == mock_recipes
        assert result["total"] == 2
        assert len(result["recipes"]) == 2
        # Verify all returned recipes are public
        for recipe in result["recipes"]:
            assert recipe.is_public == True
        assert mock_db.execute.call_count == 2  # One for recipes, one for count

    # Tests for private recipes with get_all_my_recipes
    def test_get_all_my_recipes_only_private(self):
        """Test that get_all_my_recipes returns only private recipes when user has only private recipes."""
        # Arrange
        mock_db = Mock()
        mock_recipes = [
            Recipe(id=1, uuid="uuid1", title="Private Recipe 1", description="First private recipe", 
                   ingredients=[{"name": "Flour", "amount": "1 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=10, cooking_time=20, servings=2, difficulty_level="Easy", 
                   is_public=False, user_id="user1"),
            Recipe(id=2, uuid="uuid2", title="Private Recipe 2", description="Second private recipe", 
                   ingredients=[{"name": "Sugar", "amount": "1/2 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=15, cooking_time=25, servings=4, difficulty_level="Medium", 
                   is_public=False, user_id="user1")
        ]
        
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.side_effect = [mock_recipes, mock_recipes]  # First for recipes, second for count
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act
        result = recipe_service.get_all_my_recipes(user_id="user1")
        
        # Assert
        assert result["recipes"] == mock_recipes
        assert result["total"] == 2
        assert len(result["recipes"]) == 2
        # Verify all returned recipes are private
        for recipe in result["recipes"]:
            assert recipe.is_public == False
        assert mock_db.execute.call_count == 2  # One for recipes, one for count

    def test_get_all_my_recipes_mixed_public_private(self):
        """Test that get_all_my_recipes returns both public and private recipes for a user."""
        # Arrange
        mock_db = Mock()
        mock_recipes = [
            Recipe(id=1, uuid="uuid1", title="Public Recipe 1", description="First public recipe", 
                   ingredients=[{"name": "Flour", "amount": "1 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=10, cooking_time=20, servings=2, difficulty_level="Easy", 
                   is_public=True, user_id="user1"),
            Recipe(id=2, uuid="uuid2", title="Private Recipe 1", description="First private recipe", 
                   ingredients=[{"name": "Sugar", "amount": "1/2 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=15, cooking_time=25, servings=4, difficulty_level="Medium", 
                   is_public=False, user_id="user1"),
            Recipe(id=3, uuid="uuid3", title="Public Recipe 2", description="Second public recipe", 
                   ingredients=[{"name": "Eggs", "amount": "2"}], instructions=["Mix ingredients"], 
                   preparation_time=20, cooking_time=30, servings=6, difficulty_level="Hard", 
                   is_public=True, user_id="user1"),
            Recipe(id=4, uuid="uuid4", title="Private Recipe 2", description="Second private recipe", 
                   ingredients=[{"name": "Milk", "amount": "1 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=5, cooking_time=10, servings=2, difficulty_level="Easy", 
                   is_public=False, user_id="user1")
        ]
        
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.side_effect = [mock_recipes, mock_recipes]  # First for recipes, second for count
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act
        result = recipe_service.get_all_my_recipes(user_id="user1")
        
        # Assert
        assert result["recipes"] == mock_recipes
        assert result["total"] == 4
        assert len(result["recipes"]) == 4
        # Verify we have both public and private recipes
        public_recipes = [r for r in result["recipes"] if r.is_public == True]
        private_recipes = [r for r in result["recipes"] if r.is_public == False]
        assert len(public_recipes) == 2
        assert len(private_recipes) == 2
        assert mock_db.execute.call_count == 2  # One for recipes, one for count

    # Tests for get_all_public_recipes with private recipe test data
    def test_get_all_public_recipes_filters_out_private(self):
        """Test that get_all_public_recipes correctly filters out private recipes."""
        # Arrange
        mock_db = Mock()
        # Create test data with both public and private recipes
        all_recipes = [
            Recipe(id=1, uuid="uuid1", title="Public Recipe 1", description="First public recipe", 
                   ingredients=[{"name": "Flour", "amount": "1 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=10, cooking_time=20, servings=2, difficulty_level="Easy", 
                   is_public=True, user_id="user1"),
            Recipe(id=2, uuid="uuid2", title="Private Recipe 1", description="First private recipe", 
                   ingredients=[{"name": "Sugar", "amount": "1/2 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=15, cooking_time=25, servings=4, difficulty_level="Medium", 
                   is_public=False, user_id="user1"),
            Recipe(id=3, uuid="uuid3", title="Public Recipe 2", description="Second public recipe", 
                   ingredients=[{"name": "Eggs", "amount": "2"}], instructions=["Mix ingredients"], 
                   preparation_time=20, cooking_time=30, servings=6, difficulty_level="Hard", 
                   is_public=True, user_id="user2"),
            Recipe(id=4, uuid="uuid4", title="Private Recipe 2", description="Second private recipe", 
                   ingredients=[{"name": "Milk", "amount": "1 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=5, cooking_time=10, servings=2, difficulty_level="Easy", 
                   is_public=False, user_id="user2")
        ]
        
        # Only public recipes should be returned
        public_recipes = [r for r in all_recipes if r.is_public == True]
        
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.side_effect = [public_recipes, public_recipes]  # First for recipes, second for count
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act
        result = recipe_service.get_all_public_recipes()
        
        # Assert
        assert result["recipes"] == public_recipes
        assert result["total"] == 2
        assert len(result["recipes"]) == 2
        # Verify only public recipes are returned
        for recipe in result["recipes"]:
            assert recipe.is_public == True
        # Verify private recipes are NOT included
        private_recipe_ids = [r.id for r in all_recipes if r.is_public == False]
        returned_recipe_ids = [r.id for r in result["recipes"]]
        for private_id in private_recipe_ids:
            assert private_id not in returned_recipe_ids
        assert mock_db.execute.call_count == 2  # One for recipes, one for count

    def test_get_all_public_recipes_only_private_in_db(self):
        """Test that get_all_public_recipes returns empty when only private recipes exist."""
        # Arrange
        mock_db = Mock()
        # Create test data with only private recipes
        private_recipes = [
            Recipe(id=1, uuid="uuid1", title="Private Recipe 1", description="First private recipe", 
                   ingredients=[{"name": "Flour", "amount": "1 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=10, cooking_time=20, servings=2, difficulty_level="Easy", 
                   is_public=False, user_id="user1"),
            Recipe(id=2, uuid="uuid2", title="Private Recipe 2", description="Second private recipe", 
                   ingredients=[{"name": "Sugar", "amount": "1/2 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=15, cooking_time=25, servings=4, difficulty_level="Medium", 
                   is_public=False, user_id="user1"),
            Recipe(id=3, uuid="uuid3", title="Private Recipe 3", description="Third private recipe", 
                   ingredients=[{"name": "Eggs", "amount": "2"}], instructions=["Mix ingredients"], 
                   preparation_time=20, cooking_time=30, servings=6, difficulty_level="Hard", 
                   is_public=False, user_id="user2")
        ]
        
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.side_effect = [[], []]  # No public recipes found
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act
        result = recipe_service.get_all_public_recipes()
        
        # Assert
        assert result["recipes"] == []
        assert result["total"] == 0
        assert len(result["recipes"]) == 0
        assert mock_db.execute.call_count == 2  # One for recipes, one for count

    def test_get_all_public_recipes_database_exception(self):
        """Test handling of database exceptions in get_all_public_recipes."""
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Database error")
        recipe_service = RecipeService(mock_db)
        with pytest.raises(Exception, match="Database error"):
            recipe_service.get_all_public_recipes()

    def test_get_all_public_recipes_verify_select_statement(self):
        """Test that the correct select statement is used in get_all_public_recipes."""
        mock_db = Mock()
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        recipe_service = RecipeService(mock_db)
        recipe_service.get_all_public_recipes(limit=10, offset=20)
        # Check first call (recipes with pagination)
        first_call_args = mock_db.execute.call_args_list[0][0][0]
        first_call_str = str(first_call_args).lower()
        assert "select" in first_call_str
        assert "limit" in first_call_str
        assert "offset" in first_call_str
        # Check second call (count without pagination)
        second_call_args = mock_db.execute.call_args_list[1][0][0]
        second_call_str = str(second_call_args).lower()
        assert "select" in second_call_str
        assert "limit" not in second_call_str
        assert "offset" not in second_call_str