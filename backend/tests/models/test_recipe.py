import pytest
from src.models.recipe import Recipe
from pydantic import ValidationError

def test_create_recipe_instance():
    """Test creating a Recipe instance with all fields."""
    recipe = Recipe(
        title="Test Recipe",
        description="A test recipe description",
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
    
    assert recipe.title == "Test Recipe"
    assert recipe.description == "A test recipe description"
    assert recipe.ingredients == [{"name": "Flour", "amount": "1 cup"}]
    assert recipe.instructions == ["Mix ingredients", "Bake at 350F"]
    assert recipe.preparation_time == 15
    assert recipe.cooking_time == 30
    assert recipe.servings == 4
    assert recipe.difficulty_level == "Easy"
    assert recipe.is_public is True
    assert recipe.image_url == "https://example.com/image.jpg"
    assert recipe.user_id == "test-user-uuid"
    assert recipe.uuid is not None

def test_create_recipe_instance_minimal():
    """Test creating a Recipe instance with only required fields and check defaults."""
    recipe_data = {
        "title": "Minimal Recipe",
        "ingredients": [{"name": "Ingredient 1", "amount": "100g"}],
        "instructions": ["Step 1"],
        "preparation_time": 15,
        "cooking_time": 30,
        "servings": 2,
        "user_id": "test-user-uuid"
    }
    recipe = Recipe(**recipe_data)

    assert recipe.title == recipe_data["title"]
    assert recipe.description is None  # Default for Optional[str]
    assert recipe.ingredients == recipe_data["ingredients"]
    assert recipe.instructions == recipe_data["instructions"]
    assert recipe.preparation_time == recipe_data["preparation_time"]
    assert recipe.cooking_time == recipe_data["cooking_time"]
    assert recipe.servings == recipe_data["servings"]
    assert recipe.user_id == recipe_data["user_id"]
    assert recipe.uuid is not None

def test_recipe_uuid_generation():
    """Test that UUID is automatically generated for new recipes."""
    recipe_data = {
        "title": "UUID Test Recipe",
        "ingredients": [{"name": "Ingredient 1", "amount": "100g"}],
        "instructions": ["Step 1"],
        "preparation_time": 15,
        "cooking_time": 30,
        "servings": 2,
        "user": "test-user-uuid"
    }
    recipe = Recipe(**recipe_data)
    
    assert recipe.uuid is not None
    assert isinstance(recipe.uuid, str)
    assert len(recipe.uuid) > 0

def test_recipe_string_representation():
    """Test the string representation of the Recipe model."""
    recipe_data = {
        "title": "Repr Test Recipe",
        "description": "Test description",
        "ingredients": [{"name": "Ingredient 1", "amount": "100g"}],
        "instructions": ["Step 1"],
        "preparation_time": 15,
        "cooking_time": 30,
        "servings": 2,
        "user": "test-user-uuid"
    }
    recipe = Recipe(**recipe_data)
    
    expected_repr = f"<Recipe title={recipe.title} description={recipe.description} uuid={recipe.uuid}>"
    assert str(recipe) == f"<Recipe title={recipe.title}>"
    assert repr(recipe) == expected_repr

def test_recipe_validation_rules():
    """Test all recipe validation rules."""
    # Test empty title
    with pytest.raises(ValidationError, match="Title cannot be empty"):
        Recipe(
            title="",
            ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
            instructions=["Step 1"],
            preparation_time=15,
            cooking_time=30,
            servings=2,
            user_id="test-user-uuid"
        )

    # Test title too short
    with pytest.raises(ValidationError, match="Title must be at least 3 characters long"):
        Recipe(
            title="ab",
            ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
            instructions=["Step 1"],
            preparation_time=15,
            cooking_time=30,
            servings=2,
            user_id="test-user-uuid"
        )

    # Test empty ingredients list
    with pytest.raises(ValidationError, match="Ingredients list cannot be empty"):
        Recipe(
            title="Test Recipe",
            ingredients=[],
            instructions=["Step 1"],
            preparation_time=15,
            cooking_time=30,
            servings=2,
            user_id="test-user-uuid"
        )

    # Test invalid ingredient format
    # with pytest.raises(ValidationError, match="Each ingredient must be a dictionary"):
    #     Recipe(
    #         title="Test Recipe",
    #         ingredients=["Invalid ingredient"],
    #         instructions=["Step 1"],
    #         preparation_time=15,
    #         cooking_time=30,
    #         servings=2,
    #         user_id="test-user-uuid"
    #     )

    # Test ingredient missing required fields
    with pytest.raises(ValidationError, match="Each ingredient must have \"name\" and \"amount\" fields"):
        Recipe(
            title="Test Recipe",
            ingredients=[{"invalid": "field"}],
            instructions=["Step 1"],
            preparation_time=15,
            cooking_time=30,
            servings=2,
            user_id="test-user-uuid"
        )

    # Test empty ingredient fields
    with pytest.raises(ValidationError, match="Ingredient name and amount cannot be empty"):
        Recipe(
            title="Test Recipe",
            ingredients=[{"name": "", "amount": ""}],
            instructions=["Step 1"],
            preparation_time=15,
            cooking_time=30,
            servings=2,
            user_id="test-user-uuid"
        )

    # Test empty instructions list
    with pytest.raises(ValidationError, match="Instructions list cannot be empty"):
        Recipe(
            title="Test Recipe",
            ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
            instructions=[],
            preparation_time=15,
            cooking_time=30,
            servings=2,
            user_id="test-user-uuid"
        )

    # # Test invalid instruction format
    # with pytest.raises(ValidationError, match="Each instruction must be a string"):
    #     Recipe(
    #         title="Test Recipe",
    #         ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
    #         instructions=[123],  # Invalid type
    #         preparation_time=15,
    #         cooking_time=30,
    #         servings=2,
    #         user_id="test-user-uuid"
    #     )

    # Test empty instruction
    with pytest.raises(ValidationError, match="Instruction cannot be empty or only whitespace"):
        Recipe(
            title="Test Recipe",
            ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
            instructions=["   "],  # Only whitespace
            preparation_time=15,
            cooking_time=30,
            servings=2,
            user_id="test-user-uuid"
        )

    # Test negative preparation time
    with pytest.raises(ValidationError, match="Time must be positive"):
        Recipe(
            title="Test Recipe",
            ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
            instructions=["Step 1"],
            preparation_time=-15,
            cooking_time=30,
            servings=2,
            user_id="test-user-uuid"
        )

    # Test preparation time too long
    # with pytest.raises(ValidationError, match="Time cannot exceed 3 days (1440 minutes)"):
    #     Recipe(
    #         title="Test Recipe",
    #         ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
    #         instructions=["Step 1"],
    #         preparation_time=4500,  # more than 3 days
    #         cooking_time=30,
    #         servings=2,
    #         user_id="test-user-uuid"
    #     )

    # Test negative cooking time
    with pytest.raises(ValidationError, match="Time must be positive"):
        Recipe(
            title="Test Recipe",
            ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
            instructions=["Step 1"],
            preparation_time=15,
            cooking_time=-30,
            servings=2,
            user_id="test-user-uuid"
        )

    # Test cooking time too long
    # with pytest.raises(ValidationError, match="Time cannot exceed 3 days (1440 minutes)"):
    #     print("=================before recipe")
    #     Recipe(
    #         title="Test Recipe",
    #         ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
    #         instructions=["Step 1"],
    #         preparation_time=15,
    #         cooking_time=4500,  # more than 3 days
    #         servings=2,
    #         user_id="test-user-uuid"
    #     )
    #     print("=================after recipe")

    # Test negative servings
    with pytest.raises(ValidationError, match="Servings must be positive"):
        Recipe(
            title="Test Recipe",
            ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
            instructions=["Step 1"],
            preparation_time=15,
            cooking_time=30,
            servings=-2,
            user_id="test-user-uuid"
        )

    # Test servings too high
    with pytest.raises(ValidationError, match="Servings cannot exceed 100"):
        Recipe(
            title="Test Recipe",
            ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
            instructions=["Step 1"],
            preparation_time=15,
            cooking_time=30,
            servings=101,
            user_id="test-user-uuid"
        )

    # Note: user_id validation is handled at the database level, not Pydantic level 

def test_recipe_comparison():
    """Test recipe comparison functionality."""
    recipe1 = Recipe(
        title="Same Recipe",
        description="Some description",
        ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
        instructions=["Step 1"],
        preparation_time=15,
        cooking_time=30,
        servings=2,
        user_id="test-user-uuid"
    )
    recipe2 = Recipe(
        title="Same Recipe",
        description="Another description",
        ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
        instructions=["Step 1"],
        preparation_time=15,
        cooking_time=30,
        servings=2,
        user_id="test-user-uuid"
    )
    recipe3 = Recipe(
        title="Different Recipe",
        description="Another description",
        ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
        instructions=["Step 1"],
        preparation_time=15,
        cooking_time=30,
        servings=2,
        user_id="test-user-uuid"
    )
    recipe4 = Recipe(
        title="Same Recipe",
        ingredients=[{"name": "Ingredient 1", "amount": "100g"}],
        instructions=["Step 1"],
        preparation_time=15,
        cooking_time=30,
        servings=2,
        user_id="test-user-uuid2"
    )
    
    # Test equality
    assert recipe1 == recipe2
    assert recipe1 != recipe3
    assert recipe1 != recipe4
    # Test that different description don't affect equality
    assert recipe1.description != recipe2.description
    assert recipe1 == recipe2  # Should still be equal despite different description 