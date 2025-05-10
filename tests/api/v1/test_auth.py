import pytest
import uuid
from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.config import settings
from app.core.security import get_password_hash
from app.core.supabase_client import get_supabase_admin_client

# This assumes that your .env file is loaded correctly when pytest runs,
# or you have pytest-dotenv configured.

TOKEN_URL = f"{settings.API_V1_STR}/users/token"

@pytest.fixture(scope="module")
def supabase_admin_client():
    """Provides a Supabase admin client instance for the test module."""
    # Ensure environment variables are loaded for the client
    # This client is for direct DB manipulation in tests, bypassing RLS.
    client = get_supabase_admin_client()
    return client

@pytest.fixture
def test_user(supabase_admin_client):
    """
    Creates a user in the database for testing and cleans up afterwards.
    Yields a dictionary with user details (email, password, id, is_active).
    """
    test_email = f"test_user_{uuid.uuid4()}@example.com"
    test_password = "TestPassword123!"
    hashed_password = get_password_hash(test_password)
    current_time = datetime.utcnow().isoformat()
    user_data = {
        "email": test_email,
        "hashed_password": hashed_password,
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "created_at": current_time,
        "updated_at": current_time,
        "uuid": str(uuid.uuid4())
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
            "is_active": True
        }
    finally:
        if created_user and created_user.get("id"):
            supabase_admin_client.from_("users").delete().eq("id", created_user["id"]).execute()

@pytest.fixture
def inactive_test_user(supabase_admin_client):
    """
    Creates an inactive user in the database for testing and cleans up afterwards.
    Yields a dictionary with user details (email, password, id, is_active).
    """
    test_email = f"inactive_user_{uuid.uuid4()}@example.com"
    test_password = "TestPassword123!"
    hashed_password = get_password_hash(test_password)
    current_time = datetime.utcnow().isoformat()
    user_data = {
        "email": test_email,
        "hashed_password": hashed_password,
        "full_name": "Inactive Test User",
        "is_active": False,
        "is_superuser": False,
        "created_at": current_time,
        "updated_at": current_time
    }
    
    created_user = None
    try:
        response = supabase_admin_client.from_("users").insert(user_data, returning="representation").execute()
        assert response.data, f"Failed to create inactive test user: {getattr(response, 'error', 'Unknown error')}"
        created_user = response.data[0]
        yield {
            "id": created_user["id"],
            "email": test_email,
            "password": test_password,
            "is_active": False
        }
    finally:
        if created_user and created_user.get("id"):
            supabase_admin_client.from_("users").delete().eq("id", created_user["id"]).execute()

def test_login_success(client: TestClient, test_user):
    """Test successful login with correct credentials."""
    login_data = {"username": test_user["email"], "password": test_user["password"]}
    response = client.post(TOKEN_URL, data=login_data)
    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient, test_user):
    login_data = {"username": test_user["email"], "password": "wrongpassword"}
    response = client.post(TOKEN_URL, data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Incorrect email or password"

def test_login_non_existent_user(client: TestClient):
    login_data = {"username": f"nonexistent_{uuid.uuid4()}@example.com", "password": "anypassword"}
    response = client.post(TOKEN_URL, data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert error_data["detail"] == "Incorrect email or password"

def test_login_inactive_user(client: TestClient, inactive_test_user):
    login_data = {"username": inactive_test_user["email"], "password": inactive_test_user["password"]}
    response = client.post(TOKEN_URL, data=login_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error_data = response.json()
    assert error_data["detail"] == "Inactive user" 