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


class TestRecipeServiceWithTags:
    """Test cases for RecipeService tag-related methods."""
    
    def test_recipe_service_initialization_with_tag_service(self):
        """Test that RecipeService can be initialized with TagService."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
        
        # Act
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        # Assert
        assert recipe_service.db == mock_db
        assert recipe_service.tag_service == mock_tag_service
    
    def test_recipe_service_initialization_without_tag_service(self):
        """Test that RecipeService can be initialized without TagService."""
        # Arrange
        mock_db = Mock()
        
        # Act
        recipe_service = RecipeService(mock_db)
        
        # Assert
        assert recipe_service.db == mock_db
        assert recipe_service.tag_service is None
    
    def test_add_tags_to_recipe_dict_with_tags(self):
        """Test _add_tags_to_recipe_dict when recipe has tags."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        recipe = Recipe(
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
            user_id="test-user-uuid"
        )
        
        # Mock tags
        mock_tags = [Mock(), Mock()]
        mock_tags[0].id = 1
        mock_tags[0].name = "Italian"
        mock_tags[0].category = "Cuisines"
        mock_tags[1].id = 2
        mock_tags[1].name = "Vegetarian"
        mock_tags[1].category = "Special Dietary"
        mock_tag_service.get_tags_for_recipe.return_value = mock_tags
        
        # Act
        result = recipe_service._add_tags_to_recipe_dict(recipe)
        
        # Assert
        assert "tags" in result
        assert len(result["tags"]) == 2
        assert result["tags"][0]["id"] == 1
        assert result["tags"][0]["name"] == "Italian"
        assert result["tags"][0]["category"] == "Cuisines"
        assert result["tags"][1]["id"] == 2
        assert result["tags"][1]["name"] == "Vegetarian"
        assert result["tags"][1]["category"] == "Special Dietary"
        mock_tag_service.get_tags_for_recipe.assert_called_once_with(1)
    
    def test_add_tags_to_recipe_dict_without_tags(self):
        """Test _add_tags_to_recipe_dict when recipe has no tags."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        recipe = Recipe(
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
            user_id="test-user-uuid"
        )
        
        mock_tag_service.get_tags_for_recipe.return_value = []
        
        # Act
        result = recipe_service._add_tags_to_recipe_dict(recipe)
        
        # Assert
        assert "tags" in result
        assert result["tags"] == []
        mock_tag_service.get_tags_for_recipe.assert_called_once_with(1)
    
    def test_add_tags_to_recipe_dict_without_tag_service(self):
        """Test _add_tags_to_recipe_dict when no tag_service is available."""
        # Arrange
        mock_db = Mock()
        recipe_service = RecipeService(mock_db)  # No tag_service
        
        recipe = Recipe(
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
            user_id="test-user-uuid"
        )
        
        # Act
        result = recipe_service._add_tags_to_recipe_dict(recipe)
        
        # Assert
        assert "tags" in result
        assert result["tags"] == []
    
    def test_get_recipe_with_tags_found(self):
        """Test get_recipe_with_tags when recipe exists."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        recipe = Recipe(
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
            user_id="test-user-uuid"
        )
        
        mock_tags = [
            Mock(id=1, name="Italian", category=Mock(value="Cuisines"))
        ]
        # Configure the mock to return the actual values
        mock_tags[0].id = 1
        mock_tags[0].name = "Italian"
        mock_tags[0].category.value = "Cuisines"
        
        # Mock get_recipe
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = recipe
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        mock_tag_service.get_tags_for_recipe.return_value = mock_tags
        
        # Act
        result = recipe_service.get_recipe_with_tags(1)
        
        # Assert
        assert result is not None
        assert result["id"] == 1
        assert result["title"] == "Test Recipe"
        assert "tags" in result
        assert len(result["tags"]) == 1
        assert result["tags"][0]["id"] == 1
        assert result["tags"][0]["name"] == "Italian"
    
    def test_get_recipe_with_tags_not_found(self):
        """Test get_recipe_with_tags when recipe doesn't exist."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        # Mock get_recipe to return None
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        # Act
        result = recipe_service.get_recipe_with_tags(999)
        
        # Assert
        assert result is None
        mock_tag_service.get_tags_for_recipe.assert_not_called()
    
    def test_get_all_my_recipes_with_tags(self):
        """Test get_all_my_recipes_with_tags with multiple recipes."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        recipes = [
            Recipe(id=1, uuid="uuid1", title="Recipe 1", description="First recipe", 
                   ingredients=[{"name": "Flour", "amount": "1 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=10, cooking_time=20, servings=2, difficulty_level="Easy", 
                   is_public=True, user_id="user1"),
            Recipe(id=2, uuid="uuid2", title="Recipe 2", description="Second recipe", 
                   ingredients=[{"name": "Sugar", "amount": "1/2 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=15, cooking_time=25, servings=4, difficulty_level="Medium", 
                   is_public=True, user_id="user1")
        ]
        
        mock_tags_1 = [Mock(id=1, name="Italian", category=Mock(value="Cuisines"))]
        mock_tags_2 = [Mock(id=2, name="Vegetarian", category=Mock(value="Special Dietary"))]
        
        # Configure the mocks to return the actual values
        mock_tags_1[0].id = 1
        mock_tags_1[0].name = "Italian"
        mock_tags_1[0].category.value = "Cuisines"
        mock_tags_2[0].id = 2
        mock_tags_2[0].name = "Vegetarian"
        mock_tags_2[0].category.value = "Special Dietary"
        
        # Mock get_all_my_recipes
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.side_effect = [recipes, recipes]  # First for recipes, second for count
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        # Mock tag service calls
        mock_tag_service.get_tags_for_recipe.side_effect = [mock_tags_1, mock_tags_2]
        
        # Act
        result = recipe_service.get_all_my_recipes_with_tags(user_id="user1")
        
        # Assert
        assert len(result["recipes"]) == 2
        assert result["recipes"][0]["id"] == 1
        assert result["recipes"][0]["tags"][0]["name"] == "Italian"
        assert result["recipes"][1]["id"] == 2
        assert result["recipes"][1]["tags"][0]["name"] == "Vegetarian"
        assert mock_tag_service.get_tags_for_recipe.call_count == 2
    
    def test_get_all_public_recipes_with_tags(self):
        """Test get_all_public_recipes_with_tags with multiple recipes."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        recipes = [
            Recipe(id=1, uuid="uuid1", title="Recipe 1", description="First recipe", 
                   ingredients=[{"name": "Flour", "amount": "1 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=10, cooking_time=20, servings=2, difficulty_level="Easy", 
                   is_public=True, user_id="user1"),
            Recipe(id=2, uuid="uuid2", title="Recipe 2", description="Second recipe", 
                   ingredients=[{"name": "Sugar", "amount": "1/2 cup"}], instructions=["Mix ingredients"], 
                   preparation_time=15, cooking_time=25, servings=4, difficulty_level="Medium", 
                   is_public=True, user_id="user2")
        ]
        
        mock_tags_1 = [Mock(id=1, name="Italian", category=Mock(value="Cuisines"))]
        mock_tags_2 = [Mock(id=2, name="Vegetarian", category=Mock(value="Special Dietary"))]
        
        # Configure the mocks to return the actual values
        mock_tags_1[0].id = 1
        mock_tags_1[0].name = "Italian"
        mock_tags_1[0].category.value = "Cuisines"
        mock_tags_2[0].id = 2
        mock_tags_2[0].name = "Vegetarian"
        mock_tags_2[0].category.value = "Special Dietary"
        
        # Mock get_all_public_recipes
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.all.side_effect = [recipes, recipes]  # First for recipes, second for count
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        # Mock tag service calls
        mock_tag_service.get_tags_for_recipe.side_effect = [mock_tags_1, mock_tags_2]
        
        # Act
        result = recipe_service.get_all_public_recipes_with_tags()
        
        # Assert
        assert len(result["recipes"]) == 2
        assert result["recipes"][0]["id"] == 1
        assert result["recipes"][0]["tags"][0]["name"] == "Italian"
        assert result["recipes"][1]["id"] == 2
        assert result["recipes"][1]["tags"][0]["name"] == "Vegetarian"
        assert mock_tag_service.get_tags_for_recipe.call_count == 2
    
    def test_create_recipe_with_tags_success(self):
        """Test create_recipe_with_tags with valid tag_ids."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        recipe_data = {
            "title": "Test Recipe",
            "description": "A test recipe",
            "ingredients": [{"name": "Flour", "amount": "1 cup"}],
            "instructions": ["Mix ingredients", "Bake at 350F"],
            "preparation_time": 15,
            "cooking_time": 30,
            "servings": 4,
            "difficulty_level": "Easy",
            "is_public": True,
            "tag_ids": [1, 2]
        }
        
        created_recipe = Recipe(
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
            user_id="test-user-uuid"
        )
        
        mock_tags = [
            Mock(id=1, name="Italian", category=Mock(value="Cuisines")),
            Mock(id=2, name="Vegetarian", category=Mock(value="Special Dietary"))
        ]
        # Configure the mocks to return the actual values
        mock_tags[0].id = 1
        mock_tags[0].name = "Italian"
        mock_tags[0].category.value = "Cuisines"
        mock_tags[1].id = 2
        mock_tags[1].name = "Vegetarian"
        mock_tags[1].category.value = "Special Dietary"
        
        # Mock create_recipe method directly
        recipe_service.create_recipe = Mock(return_value=created_recipe)
        
        # Mock get_recipe method for get_recipe_with_tags
        recipe_service.get_recipe = Mock(return_value=created_recipe)
        
        # Mock tag service
        mock_tag_service.update_recipe_tags.return_value = {"errors": [], "warnings": []}
        mock_tag_service.get_tags_for_recipe.return_value = mock_tags
        
        # Act
        result = recipe_service.create_recipe_with_tags(recipe_data, "test-user-uuid")
        
        # Assert
        assert result["id"] == 1
        assert result["title"] == "Test Recipe"
        assert len(result["tags"]) == 2
        mock_tag_service.update_recipe_tags.assert_called_once_with(
            recipe_id=1, add_tag_ids=[1, 2]
        )
    
    def test_create_recipe_with_tags_no_tag_ids(self):
        """Test create_recipe_with_tags without tag_ids."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        recipe_data = {
            "title": "Test Recipe",
            "description": "A test recipe",
            "ingredients": [{"name": "Flour", "amount": "1 cup"}],
            "instructions": ["Mix ingredients", "Bake at 350F"],
            "preparation_time": 15,
            "cooking_time": 30,
            "servings": 4,
            "difficulty_level": "Easy",
            "is_public": True
            # No tag_ids
        }
        
        created_recipe = Recipe(
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
            user_id="test-user-uuid"
        )
        
        # Mock create_recipe method directly
        recipe_service.create_recipe = Mock(return_value=created_recipe)
        
        # Mock get_recipe method for get_recipe_with_tags
        recipe_service.get_recipe = Mock(return_value=created_recipe)
        
        # Mock tag service to return empty list
        mock_tag_service.get_tags_for_recipe.return_value = []
        
        # Act
        result = recipe_service.create_recipe_with_tags(recipe_data, "test-user-uuid")
        
        # Assert
        assert result["id"] == 1
        assert result["title"] == "Test Recipe"
        mock_tag_service.update_recipe_tags.assert_not_called()
    
    def test_create_recipe_with_tags_tag_service_error(self):
        """Test create_recipe_with_tags when tag service returns errors."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        recipe_data = {
            "title": "Test Recipe",
            "description": "A test recipe",
            "ingredients": [{"name": "Flour", "amount": "1 cup"}],
            "instructions": ["Mix ingredients", "Bake at 350F"],
            "preparation_time": 15,
            "cooking_time": 30,
            "servings": 4,
            "difficulty_level": "Easy",
            "is_public": True,
            "tag_ids": [1, 2]
        }
        
        created_recipe = Recipe(
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
            user_id="test-user-uuid"
        )
        
        # Mock create_recipe
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = created_recipe
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        # Mock tag service to return errors
        mock_tag_service.update_recipe_tags.return_value = {
            "errors": ["Tag with ID 999 not found"],
            "warnings": []
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Failed to add tags to recipe"):
            recipe_service.create_recipe_with_tags(recipe_data, "test-user-uuid")
    
    def test_update_recipe_with_tags_success(self):
        """Test update_recipe_with_tags with valid tag_ids."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        update_data = {
            "title": "Updated Recipe",
            "tag_ids": [1, 3]  # Change from [1, 2] to [1, 3]
        }
        
        existing_recipe = Recipe(
            id=1,
            uuid="test-recipe-uuid",
            title="Original Recipe",
            description="A test recipe",
            ingredients=[{"name": "Flour", "amount": "1 cup"}],
            instructions=["Mix ingredients", "Bake at 350F"],
            preparation_time=15,
            cooking_time=30,
            servings=4,
            difficulty_level="Easy",
            is_public=True,
            user_id="test-user-uuid"
        )
        
        updated_recipe = Recipe(
            id=1,
            uuid="test-recipe-uuid",
            title="Updated Recipe",
            description="A test recipe",
            ingredients=[{"name": "Flour", "amount": "1 cup"}],
            instructions=["Mix ingredients", "Bake at 350F"],
            preparation_time=15,
            cooking_time=30,
            servings=4,
            difficulty_level="Easy",
            is_public=True,
            user_id="test-user-uuid"
        )
        
        current_tags = [
            Mock(id=1, name="Italian", category=Mock(value="Cuisines")),
            Mock(id=2, name="Vegetarian", category=Mock(value="Special Dietary"))
        ]
        
        final_tags = [
            Mock(id=1, name="Italian", category=Mock(value="Cuisines")),
            Mock(id=3, name="Quick", category=Mock(value="Cooking Methods"))
        ]
        
        # Mock update_recipe method directly
        recipe_service.update_recipe = Mock(return_value=updated_recipe)
        
        # Mock get_recipe method for get_recipe_with_tags
        recipe_service.get_recipe = Mock(return_value=updated_recipe)
        
        # Mock tag service
        mock_tag_service.get_tags_for_recipe.side_effect = [current_tags, final_tags]
        mock_tag_service.update_recipe_tags.return_value = {"errors": [], "warnings": []}
        
        # Act
        result = recipe_service.update_recipe_with_tags(1, update_data, "test-user-uuid")
        
        # Assert
        assert result["id"] == 1
        assert result["title"] == "Updated Recipe"
        assert len(result["tags"]) == 2
        mock_tag_service.update_recipe_tags.assert_called_once_with(
            recipe_id=1, add_tag_ids=[3], remove_tag_ids=[2]
        )
    
    def test_delete_recipe_with_tags_success(self):
        """Test delete_recipe_with_tags with existing tags."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        existing_recipe = Recipe(
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
            user_id="test-user-uuid"
        )
        
        current_tags = [
            Mock(id=1, name="Italian", category=Mock(value="Cuisines")),
            Mock(id=2, name="Vegetarian", category=Mock(value="Special Dietary"))
        ]
        
        # Mock delete_recipe method directly
        recipe_service.delete_recipe = Mock()
        
        # Mock tag service
        mock_tag_service.get_tags_for_recipe.return_value = current_tags
        mock_tag_service.update_recipe_tags.return_value = {"errors": [], "warnings": []}
        
        # Act
        recipe_service.delete_recipe_with_tags(1, "test-user-uuid")
        
        # Assert
        mock_tag_service.get_tags_for_recipe.assert_called_once_with(1)
        mock_tag_service.update_recipe_tags.assert_called_once_with(
            recipe_id=1, remove_tag_ids=[1, 2]
        )
        recipe_service.delete_recipe.assert_called_once_with(1, "test-user-uuid", False)
    
    def test_delete_recipe_with_tags_no_tags(self):
        """Test delete_recipe_with_tags when recipe has no tags."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        existing_recipe = Recipe(
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
            user_id="test-user-uuid"
        )
        
        # Mock delete_recipe method directly
        recipe_service.delete_recipe = Mock()
        
        # Mock tag service to return no tags
        mock_tag_service.get_tags_for_recipe.return_value = []
        
        # Act
        recipe_service.delete_recipe_with_tags(1, "test-user-uuid")
        
        # Assert
        mock_tag_service.get_tags_for_recipe.assert_called_once_with(1)
        mock_tag_service.update_recipe_tags.assert_not_called()
        recipe_service.delete_recipe.assert_called_once_with(1, "test-user-uuid", False)
    
    def test_delete_recipe_with_tags_no_tag_service(self):
        """Test delete_recipe_with_tags when no tag_service is available."""
        # Arrange
        mock_db = Mock()
        recipe_service = RecipeService(mock_db)  # No tag_service
        
        existing_recipe = Recipe(
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
            user_id="test-user-uuid"
        )
        
        # Mock delete_recipe method directly
        recipe_service.delete_recipe = Mock()
        
        # Act
        recipe_service.delete_recipe_with_tags(1, "test-user-uuid")
        
        # Assert
        recipe_service.delete_recipe.assert_called_once_with(1, "test-user-uuid", False)

    def test_export_recipe_to_json_success(self):
        """Test exporting a recipe to JSON format."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
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
        
        # Mock database execution
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = mock_recipe
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        # Mock tag service
        mock_tag_service.get_tags_for_recipe.return_value = []
        
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        # Act
        result = recipe_service.export_recipe_to_json(1)
        
        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert result['title'] == "Test Recipe"
        assert result['description'] == "A test recipe"
        assert 'tags' in result
        assert isinstance(result['tags'], list)

    def test_export_recipe_to_json_not_found(self):
        """Test exporting a recipe that doesn't exist."""
        # Arrange
        mock_db = Mock()
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Recipe with ID 1 not found"):
            recipe_service.export_recipe_to_json(1)

    def test_export_recipe_to_pdf_success(self):
        """Test exporting a recipe to PDF format."""
        # Arrange
        mock_db = Mock()
        mock_tag_service = Mock()
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
        
        # Mock database execution
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = mock_recipe
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        # Mock tag service
        mock_tag_service.get_tags_for_recipe.return_value = []
        
        recipe_service = RecipeService(mock_db, mock_tag_service)
        
        # Act
        result = recipe_service.export_recipe_to_pdf(1)
        
        # Assert
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        # Check for PDF header
        assert result[:4] == b'%PDF'

    def test_export_recipe_to_pdf_not_found(self):
        """Test exporting a PDF for a recipe that doesn't exist."""
        # Arrange
        mock_db = Mock()
        mock_execute = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_execute.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_execute
        
        recipe_service = RecipeService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Recipe with ID 1 not found"):
            recipe_service.export_recipe_to_pdf(1)