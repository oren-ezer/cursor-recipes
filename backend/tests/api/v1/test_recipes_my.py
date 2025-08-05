import pytest
import uuid
import time
from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from sqlmodel import Session as SQLModelSession

from src.core.config import settings
from src.core.security import hash_password, create_access_token
from src.utils.database_session import engine
from src.models.user import User
from src.models.recipe import Recipe

MY_RECIPES_URL = f"{settings.API_V1_STR}/recipes/my"
TOKEN_URL = f"{settings.API_V1_STR}/users/token"

@pytest.fixture(scope="function")
def db_session():
    """Provides a database session for tests."""
    with SQLModelSession(engine) as session:
        yield session

def cleanup_test_data(db_session: Session):
    """Clean up test data."""
    try:
        # Delete test recipes that start with 'test-recipe-'
        from sqlmodel import select
        test_recipes = db_session.exec(
            select(Recipe).where(Recipe.title.like("test-recipe-%"))
        ).all()
        for recipe in test_recipes:
            db_session.delete(recipe)
        db_session.flush()
        print("Test data cleanup completed")
    except Exception as e:
        print(f"Warning: Failed to cleanup test data: {e}")

@pytest.fixture(autouse=True)
def cleanup_before_test(db_session: Session):
    """Automatically clean up test data before each test."""
    cleanup_test_data(db_session)
    yield

@pytest.fixture
def test_user(db_session: Session):
    """
    Creates a user in the database for testing and cleans up afterwards.
    Yields a dictionary with user details.
    """
    test_email = f"test_user_{uuid.uuid4()}@example.com"
    test_password = "TestPassword123!"
    hashed_password = hash_password(test_password)
    current_time = datetime.now(timezone.utc)
    user_uuid = str(uuid.uuid4())

    user_data = {
        "email": test_email,
        "hashed_password": hashed_password,
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "created_at": current_time,
        "updated_at": current_time,
        "uuid": user_uuid
    }
    
    created_user = None
    try:
        print(f'===============================BEFORE Creating test user: {user_data}')
        # Create user using SQLAlchemy
        new_user = User(**user_data)
        db_session.add(new_user)
        db_session.flush()
        db_session.refresh(new_user)
        created_user = new_user
        print(f'===============================AFTER Creating test user: {created_user.id}')
        
        # Commit to ensure the user is persisted
        db_session.commit()

        yield {
            "id": created_user.id,
            "email": test_email,
            "password": test_password,
            "uuid": user_uuid,
            "full_name": "Test User",
            "is_active": True,
            "is_superuser": False
        }
    finally:
        if created_user and created_user.id:
            # Clean up using SQLAlchemy
            db_session.delete(created_user)
            db_session.commit()

@pytest.fixture
def auth_token(test_user):
    """Creates a valid authentication token for the test user."""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": test_user["email"],
        "user_id": test_user["id"],
        "uuid": test_user["uuid"]
    }
    return create_access_token(data=token_data, expires_delta=access_token_expires)

@pytest.fixture(scope="function")
def test_recipes(db_session: Session, test_user):
    """
    Creates test recipes in the database for testing and cleans up afterwards.
    Yields a list of recipe dictionaries.
    """
    current_time = datetime.now(timezone.utc)
    # Use timestamp in title to ensure uniqueness across test runs
    timestamp = int(time.time() * 1000)
    
    recipes_data = [
        {
            "title": f"test-recipe-{timestamp}-1",
            "description": "Test recipe 1 description",
            "ingredients": [{"name": "Ingredient 1", "amount": "1 cup"}],
            "instructions": ["Step 1", "Step 2"],
            "preparation_time": 15,
            "cooking_time": 30,
            "servings": 4,
            "difficulty_level": "Easy",
            "is_public": True,
            "user_id": test_user["uuid"],
            "created_at": current_time,
            "updated_at": current_time
        },
        {
            "title": f"test-recipe-{timestamp}-2",
            "description": "Test recipe 2 description",
            "ingredients": [{"name": "Ingredient 2", "amount": "2 cups"}],
            "instructions": ["Step 1", "Step 2", "Step 3"],
            "preparation_time": 20,
            "cooking_time": 45,
            "servings": 6,
            "difficulty_level": "Medium",
            "is_public": False,
            "user_id": test_user["uuid"],
            "created_at": current_time,
            "updated_at": current_time
        }
    ]
    
    created_recipes = []
    try:
        for recipe_data in recipes_data:
            # Create recipe using SQLAlchemy
            new_recipe = Recipe(**recipe_data)
            db_session.add(new_recipe)
            db_session.flush()
            db_session.refresh(new_recipe)
            created_recipes.append(new_recipe)
        
        # Commit to ensure recipes are persisted
        db_session.commit()

        yield created_recipes
    finally:
        # Clean up recipes
        for recipe in created_recipes:
            if recipe and recipe.id:
                db_session.delete(recipe)
        db_session.commit()

def test_get_my_recipes_success(client: TestClient, test_user, auth_token, test_recipes):
    """Test successful retrieval of current user's recipes."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get(MY_RECIPES_URL, headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify the response structure
    assert "recipes" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    
    # Verify the data
    assert data["total"] == 2
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert len(data["recipes"]) == 2
    
    # Verify recipe data
    recipe_titles = [recipe["title"] for recipe in data["recipes"]]
    # Check that we have the expected number of recipes
    assert len(recipe_titles) == 2
    # Check that the recipes belong to the test user
    for recipe in data["recipes"]:
        assert recipe["user_id"] == test_user["uuid"]

def test_get_my_recipes_no_auth_header(client: TestClient):
    """Test that endpoint returns 401 when no authorization header is provided."""
    response = client.get(MY_RECIPES_URL)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Not authenticated"

def test_get_my_recipes_invalid_token_format(client: TestClient):
    """Test that endpoint returns 401 when token format is invalid."""
    headers = {"Authorization": "InvalidTokenFormat"}
    response = client.get(MY_RECIPES_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Not authenticated"

def test_get_my_recipes_malformed_bearer_token(client: TestClient):
    """Test that endpoint returns 401 when Bearer token is malformed."""
    headers = {"Authorization": "Bearer"}
    response = client.get(MY_RECIPES_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Not authenticated"

def test_get_my_recipes_invalid_token(client: TestClient):
    """Test that endpoint returns 401 when token is invalid."""
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = client.get(MY_RECIPES_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Not authenticated"

def test_get_my_recipes_expired_token(client: TestClient, test_user):
    """Test that endpoint returns 401 when token is expired."""
    # Create an expired token
    expired_token = create_access_token(
        data={"sub": test_user["email"], "user_id": test_user["id"], "uuid": test_user["uuid"]},
        expires_delta=timedelta(minutes=-10)  # Expired 10 minutes ago
    )
    
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get(MY_RECIPES_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Not authenticated"

def test_get_my_recipes_user_not_found_in_db(client: TestClient, db_session: Session):
    """Test that endpoint returns 401 when user exists in token but not in database."""
    # Create a token for a user that doesn't exist in the database
    fake_user_uuid = str(uuid.uuid4())
    fake_user_email = f"fake_user_{uuid.uuid4()}@example.com"
    
    token = create_access_token(
        data={"sub": fake_user_email, "user_id": 99999, "uuid": fake_user_uuid},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(MY_RECIPES_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Not authenticated"

def test_get_my_recipes_with_login_flow(client: TestClient, test_user, test_recipes):
    """Test the complete flow: login then get /my recipes endpoint."""
    # First, login to get a token
    login_data = {"username": test_user["email"], "password": test_user["password"]}
    login_response = client.post(TOKEN_URL, data=login_data)
    assert login_response.status_code == status.HTTP_200_OK
    
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    # Then use the token to access /my recipes endpoint
    headers = {"Authorization": f"Bearer {access_token}"}
    my_recipes_response = client.get(MY_RECIPES_URL, headers=headers)
    
    assert my_recipes_response.status_code == status.HTTP_200_OK
    data = my_recipes_response.json()
    
    # Verify the returned data
    assert data["total"] == 2
    assert len(data["recipes"]) == 2

def test_get_my_recipes_database_error(client: TestClient, auth_token):
    """Test that endpoint handles database errors gracefully."""
    with patch('src.services.recipes_service.RecipeService.get_all_recipes') as mock_get_all_recipes:
        # Mock the service to raise an exception
        mock_get_all_recipes.side_effect = Exception("Database connection error")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get(MY_RECIPES_URL, headers=headers)
        
        # Should return 500 Internal Server Error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        error_data = response.json()
        assert "Failed to retrieve user recipes" in error_data["detail"]

def test_get_my_recipes_missing_token_claims(client: TestClient):
    """Test that endpoint handles tokens with missing claims."""
    # Create a token with missing claims
    incomplete_token = create_access_token(
        data={"sub": "test@example.com"},  # Missing user_id and uuid
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    headers = {"Authorization": f"Bearer {incomplete_token}"}
    response = client.get(MY_RECIPES_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Not authenticated"

def test_get_my_recipes_empty_list(client: TestClient, test_user, auth_token):
    """Test that endpoint returns empty list when user has no recipes."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get(MY_RECIPES_URL, headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify the response structure
    assert "recipes" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    
    # Verify empty data
    assert data["total"] == 0
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert len(data["recipes"]) == 0

def test_get_my_recipes_pagination(client: TestClient, test_user, auth_token, db_session: Session):
    """Test pagination functionality."""
    # Create more recipes for pagination testing
    current_time = datetime.now(timezone.utc)
    recipes_data = []
    
    for i in range(15):  # Create 15 recipes
        recipes_data.append({
            "title": f"Pagination Recipe {i+1}",
            "description": f"Recipe for pagination test {i+1}",
            "ingredients": [{"name": f"Ingredient {i+1}", "amount": "100g"}],
            "instructions": [f"Step {i+1}"],
            "preparation_time": 10,
            "cooking_time": 20,
            "servings": 2,
            "difficulty_level": "Easy",
            "is_public": True,
            "user_id": test_user["uuid"],
            "created_at": current_time,
            "updated_at": current_time
        })

    created_recipes = []
    try:
        for recipe_data in recipes_data:
            # Create recipe using SQLAlchemy
            new_recipe = Recipe(**recipe_data)
            db_session.add(new_recipe)
            db_session.flush()
            db_session.refresh(new_recipe)
            created_recipes.append(new_recipe)
        
        # Commit to ensure recipes are persisted
        db_session.commit()

        # Test first page
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get(f"{MY_RECIPES_URL}?limit=10&offset=0", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total"] == 15
        assert data["limit"] == 10
        assert data["offset"] == 0
        assert len(data["recipes"]) == 10
        
        # Test second page
        response = client.get(f"{MY_RECIPES_URL}?limit=10&offset=10", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total"] == 15
        assert data["limit"] == 10
        assert data["offset"] == 10
        assert len(data["recipes"]) == 5  # Remaining 5 recipes
        
    finally:
        # Clean up using SQLAlchemy
        for recipe in created_recipes:
            if recipe.id:
                db_session.delete(recipe)
        db_session.flush()

def test_get_my_recipes_only_own_recipes(client: TestClient, db_session: Session):
    """Test that /my endpoint only returns recipes belonging to the authenticated user."""
    # Create two users
    user1_email = f"user1_{uuid.uuid4()}@example.com"
    user2_email = f"user2_{uuid.uuid4()}@example.com"
    user1_uuid = str(uuid.uuid4())
    user2_uuid = str(uuid.uuid4())
    
    users_data = [
        {
            "email": user1_email,
            "hashed_password": hash_password("TestPassword123!"),
            "full_name": "User 1",
            "is_active": True,
            "is_superuser": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "uuid": user1_uuid
        },
        {
            "email": user2_email,
            "hashed_password": hash_password("TestPassword123!"),
            "full_name": "User 2",
            "is_active": True,
            "is_superuser": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "uuid": user2_uuid
        }
    ]
    
    created_users = []
    created_recipes = []
    
    try:
        # Create users
        for user_data in users_data:
            # Create user using SQLAlchemy
            new_user = User(**user_data)
            db_session.add(new_user)
            db_session.flush()
            db_session.refresh(new_user)
            created_users.append(new_user)
        
        # Commit to ensure users are persisted
        db_session.commit()

        # Create recipes for both users
        current_time = datetime.now(timezone.utc)
        recipes_data = [
            {
                "title": "User 1 Recipe",
                "description": "Recipe belonging to user 1",
                "ingredients": [{"name": "Ingredient 1", "amount": "100g"}],
                "instructions": ["Step 1"],
                "preparation_time": 10,
                "cooking_time": 20,
                "servings": 2,
                "difficulty_level": "Easy",
                "is_public": True,
                "user_id": created_users[0].uuid,
                "created_at": current_time,
                "updated_at": current_time
            },
            {
                "title": "User 2 Recipe",
                "description": "Recipe belonging to user 2",
                "ingredients": [{"name": "Ingredient 2", "amount": "200g"}],
                "instructions": ["Step 1"],
                "preparation_time": 15,
                "cooking_time": 25,
                "servings": 3,
                "difficulty_level": "Medium",
                "is_public": True,
                "user_id": created_users[1].uuid,
                "created_at": current_time,
                "updated_at": current_time
            }
        ]

        for recipe_data in recipes_data:
            # Create recipe using SQLAlchemy
            new_recipe = Recipe(**recipe_data)
            db_session.add(new_recipe)
            db_session.flush()
            db_session.refresh(new_recipe)
            created_recipes.append(new_recipe)
        
        # Commit to ensure recipes are persisted
        db_session.commit()

        # Create token for user 1
        token1 = create_access_token(
            data={"sub": user1_email, "user_id": created_users[0].id, "uuid": user1_uuid},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # Test that user 1 only sees their own recipes
        headers = {"Authorization": f"Bearer {token1}"}
        response = client.get(MY_RECIPES_URL, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total"] == 1
        assert len(data["recipes"]) == 1
        assert data["recipes"][0]["title"] == "User 1 Recipe"
        assert data["recipes"][0]["user_id"] == user1_uuid
        
    finally:
        # Clean up recipes
        for recipe in created_recipes:
            if recipe and recipe.id:
                db_session.delete(recipe)
        db_session.commit()
        
        # Clean up users
        for user in created_users:
            if user and user.id:
                db_session.delete(user)
        db_session.commit() 