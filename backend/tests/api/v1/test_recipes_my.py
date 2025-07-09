import pytest
import uuid
import time
from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from src.core.config import settings
from src.core.security import hash_password, create_access_token
from src.core.supabase_client import get_supabase_admin_client

MY_RECIPES_URL = f"{settings.API_V1_STR}/recipes/my"
TOKEN_URL = f"{settings.API_V1_STR}/users/token"

@pytest.fixture(scope="module")
def supabase_admin_client():
    """Provides a Supabase admin client instance for the test module."""
    client = get_supabase_admin_client()
    return client

def cleanup_test_data(supabase_admin_client):
    """Clean up test data and reset sequences."""
    try:
        # Delete test recipes that start with 'test-recipe-'
        supabase_admin_client.from_("recipes").delete().like("uuid", "test-recipe-%").execute()
        print("Test data cleanup completed")
    except Exception as e:
        print(f"Warning: Failed to cleanup test data: {e}")

@pytest.fixture(autouse=True)
def cleanup_before_test(supabase_admin_client):
    """Automatically clean up test data before each test."""
    cleanup_test_data(supabase_admin_client)
    yield

@pytest.fixture
def test_user(supabase_admin_client):
    """
    Creates a user in the database for testing and cleans up afterwards.
    Yields a dictionary with user details.
    """
    test_email = f"test_user_{uuid.uuid4()}@example.com"
    test_password = "TestPassword123!"
    hashed_password = hash_password(test_password)
    current_time = datetime.now(timezone.utc).isoformat()
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
        response = supabase_admin_client.from_("users").insert(user_data, returning="representation").execute()
        print(f'===============================AFTER Creating test user: {response}')
        assert response.data, f"Failed to create test user: {getattr(response, 'error', 'Unknown error')}"
        created_user = response.data[0]
        yield {
            "id": created_user["id"],
            "email": test_email,
            "password": test_password,
            "uuid": user_uuid,
            "full_name": "Test User",
            "is_active": True,
            "is_superuser": False
        }
    finally:
        if created_user and created_user.get("id"):
            supabase_admin_client.from_("users").delete().eq("id", created_user["id"]).execute()

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
def test_recipes(supabase_admin_client, test_user):
    """
    Creates test recipes in the database for testing and cleans up afterwards.
    Yields a list of recipe dictionaries.
    """
    current_time = datetime.now(timezone.utc).isoformat()
    # Use timestamp in UUID to ensure uniqueness across test runs
    timestamp = int(time.time() * 1000)
    recipes_data = [
        {
            "uuid": f"test-recipe-1-{timestamp}-{uuid.uuid4().hex[:8]}",
            "title": "Test Recipe 1",
            "description": "A delicious test recipe",
            "ingredients": [{"name": "Ingredient 1", "amount": "100g"}],
            "instructions": ["Step 1", "Step 2"],
            "preparation_time": 15,
            "cooking_time": 30,
            "servings": 4,
            "user_id": test_user["uuid"],
            "created_at": current_time,
            "updated_at": current_time,
            "is_public": True,
            "image_url": None
        },
        {
            "uuid": f"test-recipe-2-{timestamp}-{uuid.uuid4().hex[:8]}",
            "title": "Test Recipe 2",
            "description": "Another delicious test recipe",
            "ingredients": [{"name": "Ingredient 2", "amount": "200g"}],
            "instructions": ["Step 1", "Step 2", "Step 3"],
            "preparation_time": 20,
            "cooking_time": 45,
            "servings": 6,
            "user_id": test_user["uuid"],
            "created_at": current_time,
            "updated_at": current_time,
            "is_public": False,
            "image_url": None
        }
    ]
    
    created_recipes = []
    try:
        for recipe_data in recipes_data:
            try:
                print(f'===============================================Creating test recipe: {recipe_data["uuid"]}')
                response = supabase_admin_client.from_("recipes").insert(recipe_data, returning="representation").execute()
                
                if response.data:
                    created_recipes.append(response.data[0])
                    print(f'Successfully created recipe: {response.data[0]["uuid"]}')
                else:
                    print(f'===============================================Warning: No data returned when creating recipe {recipe_data["uuid"]}')
                    if hasattr(response, 'error'):
                        print(f'===============================================Error details: {response.error}')
                        
            except Exception as e:
                print(f'===============================================Error creating recipe {recipe_data["uuid"]}: {e}')
                # Continue with other recipes even if one fails
                continue
        
        yield created_recipes
    finally:
        # Clean up recipes by UUID to avoid conflicts
        for recipe in created_recipes:
            if recipe.get("uuid"):
                try:
                    supabase_admin_client.from_("recipes").delete().eq("uuid", recipe["uuid"]).execute()
                    print(f'===============================================Successfully cleaned up recipe: {recipe["uuid"]}')
                except Exception as e:
                    # Log but don't fail if cleanup fails
                    print(f"===============================================Warning: Failed to cleanup recipe {recipe['uuid']}: {e}")

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
    assert "Test Recipe 1" in recipe_titles
    assert "Test Recipe 2" in recipe_titles
    
    # Verify all recipes belong to the test user
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

def test_get_my_recipes_user_not_found_in_db(client: TestClient, supabase_admin_client):
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
    with patch('src.utils.db.Database.select_paginated') as mock_select:
        # Simulate a database error
        mock_select.side_effect = Exception("Database connection failed")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get(MY_RECIPES_URL, headers=headers)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        error_data = response.json()
        assert "Failed to retrieve recipes" in error_data["detail"]

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

def test_get_my_recipes_pagination(client: TestClient, test_user, auth_token, supabase_admin_client):
    """Test pagination functionality."""
    # Create more recipes for pagination testing
    current_time = datetime.now(timezone.utc).isoformat()
    recipes_data = []
    
    for i in range(15):  # Create 15 recipes
        recipes_data.append({
            "uuid": str(uuid.uuid4()),
            "title": f"Pagination Recipe {i+1}",
            "description": f"Recipe for pagination test {i+1}",
            "ingredients": [{"name": f"Ingredient {i+1}", "amount": "100g"}],
            "instructions": [f"Step {i+1}"],
            "preparation_time": 10,
            "cooking_time": 20,
            "servings": 2,
            "user_id": test_user["uuid"],
            "created_at": current_time,
            "updated_at": current_time,
            "is_public": True,
            "image_url": None
        })
    
    created_recipes = []
    try:
        for recipe_data in recipes_data:
            response = supabase_admin_client.from_("recipes").insert(recipe_data, returning="representation").execute()
            assert response.data, f"Failed to create test recipe: {getattr(response, 'error', 'Unknown error')}"
            created_recipes.append(response.data[0])
        
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
        # Clean up recipes by UUID to avoid conflicts
        for recipe in created_recipes:
            if recipe.get("uuid"):
                try:
                    supabase_admin_client.from_("recipes").delete().eq("uuid", recipe["uuid"]).execute()
                except Exception as e:
                    # Log but don't fail if cleanup fails
                    print(f"Warning: Failed to cleanup recipe {recipe['uuid']}: {e}")

def test_get_my_recipes_only_own_recipes(client: TestClient, supabase_admin_client):
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
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "uuid": user1_uuid
        },
        {
            "email": user2_email,
            "hashed_password": hash_password("TestPassword123!"),
            "full_name": "User 2",
            "is_active": True,
            "is_superuser": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "uuid": user2_uuid
        }
    ]
    
    created_users = []
    created_recipes = []
    
    try:
        # Create users
        for user_data in users_data:
            response = supabase_admin_client.from_("users").insert(user_data, returning="representation").execute()
            assert response.data, "Failed to create test user"
            created_users.append(response.data[0])
        
        # Create recipes for both users
        current_time = datetime.now(timezone.utc).isoformat()
        recipes_data = [
            {
                "uuid": str(uuid.uuid4()),
                "title": "User 1 Recipe",
                "description": "Recipe belonging to user 1",
                "ingredients": [{"name": "Ingredient 1", "amount": "100g"}],
                "instructions": ["Step 1"],
                "preparation_time": 10,
                "cooking_time": 20,
                "servings": 2,
                "user_id": user1_uuid,
                "created_at": current_time,
                "updated_at": current_time,
                "is_public": True,
                "image_url": None
            },
            {
                "uuid": str(uuid.uuid4()),
                "title": "User 2 Recipe",
                "description": "Recipe belonging to user 2",
                "ingredients": [{"name": "Ingredient 2", "amount": "200g"}],
                "instructions": ["Step 1"],
                "preparation_time": 15,
                "cooking_time": 25,
                "servings": 3,
                "user_id": user2_uuid,
                "created_at": current_time,
                "updated_at": current_time,
                "is_public": True,
                "image_url": None
            }
        ]
        
        for recipe_data in recipes_data:
            response = supabase_admin_client.from_("recipes").insert(recipe_data, returning="representation").execute()
            assert response.data, "Failed to create test recipe"
            created_recipes.append(response.data[0])
        
        # Create token for user 1
        token1 = create_access_token(
            data={"sub": user1_email, "user_id": created_users[0]["id"], "uuid": user1_uuid},
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
        # Clean up recipes by UUID to avoid conflicts
        for recipe in created_recipes:
            if recipe.get("uuid"):
                try:
                    supabase_admin_client.from_("recipes").delete().eq("uuid", recipe["uuid"]).execute()
                except Exception as e:
                    # Log but don't fail if cleanup fails
                    print(f"Warning: Failed to cleanup recipe {recipe['uuid']}: {e}")
        
        # Clean up users by UUID to avoid conflicts
        for user in created_users:
            if user.get("uuid"):
                try:
                    supabase_admin_client.from_("users").delete().eq("uuid", user["uuid"]).execute()
                except Exception as e:
                    # Log but don't fail if cleanup fails
                    print(f"Warning: Failed to cleanup user {user['uuid']}: {e}") 