import pytest
import uuid
from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from src.core.config import settings
from src.core.security import hash_password, create_access_token
from src.core.supabase_client import get_supabase_admin_client

ME_URL = f"{settings.API_V1_STR}/users/me"
TOKEN_URL = f"{settings.API_V1_STR}/users/token"

@pytest.fixture(scope="module")
def supabase_admin_client():
    """Provides a Supabase admin client instance for the test module."""
    client = get_supabase_admin_client()
    return client

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
        response = supabase_admin_client.from_("users").insert(user_data, returning="representation").execute()
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

def test_get_me_success(client: TestClient, test_user, auth_token):
    """Test successful retrieval of current user information."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get(ME_URL, headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    
    # Verify the returned user data matches the test user
    assert user_data["email"] == test_user["email"]
    assert user_data["uuid"] == test_user["uuid"]
    assert user_data["full_name"] == test_user["full_name"]
    assert user_data["is_active"] == test_user["is_active"]
    assert user_data["is_superuser"] == test_user["is_superuser"]
    assert "id" in user_data
    assert "created_at" in user_data
    assert "updated_at" in user_data
    # Ensure password is not returned
    assert "hashed_password" not in user_data
    assert "password" not in user_data

def test_get_me_no_auth_header(client: TestClient):
    """Test that endpoint returns 401 when no authorization header is provided."""
    response = client.get(ME_URL)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Not authenticated"

def test_get_me_invalid_token_format(client: TestClient):
    """Test that endpoint returns 401 when token format is invalid."""
    headers = {"Authorization": "InvalidTokenFormat"}
    response = client.get(ME_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Not authenticated"

def test_get_me_malformed_bearer_token(client: TestClient):
    """Test that endpoint returns 401 when Bearer token is malformed."""
    headers = {"Authorization": "Bearer"}
    response = client.get(ME_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Not authenticated"

def test_get_me_invalid_token(client: TestClient):
    """Test that endpoint returns 401 when token is invalid."""
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = client.get(ME_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Not authenticated"

def test_get_me_expired_token(client: TestClient, test_user):
    """Test that endpoint returns 401 when token is expired."""
    # Create an expired token
    from datetime import timedelta
    expired_token = create_access_token(
        data={"sub": test_user["email"], "user_id": test_user["id"], "uuid": test_user["uuid"]},
        expires_delta=timedelta(minutes=-10)  # Expired 10 minutes ago
    )
    
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get(ME_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Not authenticated"

def test_get_me_user_not_found_in_db(client: TestClient, supabase_admin_client):
    """Test that endpoint returns 401 when user exists in token but not in database."""
    # Create a token for a user that doesn't exist in the database
    fake_user_uuid = str(uuid.uuid4())
    fake_user_email = f"fake_user_{uuid.uuid4()}@example.com"
    
    token = create_access_token(
        data={"sub": fake_user_email, "user_id": 99999, "uuid": fake_user_uuid},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(ME_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Not authenticated"

def test_get_me_with_login_flow(client: TestClient, test_user):
    """Test the complete flow: login then get /me endpoint."""
    # First, login to get a token
    login_data = {"username": test_user["email"], "password": test_user["password"]}
    login_response = client.post(TOKEN_URL, data=login_data)
    assert login_response.status_code == status.HTTP_200_OK
    
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    # Then use the token to access /me endpoint
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response = client.get(ME_URL, headers=headers)
    
    assert me_response.status_code == status.HTTP_200_OK
    user_data = me_response.json()
    
    # Verify the returned user data
    assert user_data["email"] == test_user["email"]
    assert user_data["uuid"] == test_user["uuid"]
    assert user_data["full_name"] == test_user["full_name"]

def test_get_me_database_error(client: TestClient, auth_token):
    """Test that endpoint handles database errors gracefully."""
    with patch('src.utils.db.Database.select_single') as mock_select:
        # Simulate a database error
        mock_select.side_effect = Exception("Database connection failed")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get(ME_URL, headers=headers)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        error_data = response.json()
        assert "Failed to retrieve user information" in error_data["detail"]

def test_get_me_missing_token_claims(client: TestClient):
    """Test that endpoint handles tokens with missing claims."""
    # Create a token with missing claims
    incomplete_token = create_access_token(
        data={"sub": "test@example.com"},  # Missing user_id and uuid
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    headers = {"Authorization": f"Bearer {incomplete_token}"}
    response = client.get(ME_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Not authenticated"

def test_get_me_with_different_user_data(client: TestClient, supabase_admin_client):
    """Test that /me endpoint returns the correct user data for the authenticated user."""
    # Create a second test user
    test_email_2 = f"test_user_2_{uuid.uuid4()}@example.com"
    test_password_2 = "TestPassword123!"
    hashed_password_2 = hash_password(test_password_2)
    current_time = datetime.now(timezone.utc).isoformat()
    user_uuid_2 = str(uuid.uuid4())

    user_data_2 = {
        "email": test_email_2,
        "hashed_password": hashed_password_2,
        "full_name": "Test User 2",
        "is_active": True,
        "is_superuser": False,
        "created_at": current_time,
        "updated_at": current_time,
        "uuid": user_uuid_2
    }
    
    created_user_2 = None
    try:
        response = supabase_admin_client.from_("users").insert(user_data_2, returning="representation").execute()
        assert response.data, "Failed to create second test user"
        created_user_2 = response.data[0]
        
        # Create token for the second user
        token_2 = create_access_token(
            data={"sub": test_email_2, "user_id": created_user_2["id"], "uuid": user_uuid_2},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        headers = {"Authorization": f"Bearer {token_2}"}
        response = client.get(ME_URL, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        user_data = response.json()
        
        # Verify it returns the second user's data, not the first user's
        assert user_data["email"] == test_email_2
        assert user_data["uuid"] == user_uuid_2
        assert user_data["full_name"] == "Test User 2"
        
    finally:
        if created_user_2 and created_user_2.get("id"):
            supabase_admin_client.from_("users").delete().eq("id", created_user_2["id"]).execute() 