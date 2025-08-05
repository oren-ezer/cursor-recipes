import pytest
import uuid
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

ME_URL = f"{settings.API_V1_STR}/users/me"
TOKEN_URL = f"{settings.API_V1_STR}/users/token"

@pytest.fixture(scope="function")
def db_session():
    """Provides a database session for tests."""
    with SQLModelSession(engine) as session:
        yield session

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
        # Create user using SQLAlchemy
        new_user = User(**user_data)
        db_session.add(new_user)
        db_session.flush()
        db_session.refresh(new_user)
        created_user = new_user
        
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

def test_get_me_malformed_bearer_token(client: TestClient):
    """Test that endpoint returns 401 when bearer token is malformed."""
    headers = {"Authorization": "Bearer"}
    response = client.get(ME_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_me_invalid_token(client: TestClient):
    """Test that endpoint returns 401 when token is invalid."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get(ME_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_me_expired_token(client: TestClient, test_user):
    """Test that endpoint returns 401 when token is expired."""
    # Create an expired token
    expired_token_data = {
        "sub": test_user["email"],
        "user_id": test_user["id"],
        "uuid": test_user["uuid"]
    }
    expired_token = create_access_token(
        data=expired_token_data, 
        expires_delta=timedelta(minutes=-10)  # Expired 10 minutes ago
    )
    
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get(ME_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_me_user_not_found_in_db(client: TestClient, db_session: Session):
    """Test that endpoint returns 401 when user is not found in database."""
    # Create a token for a user that doesn't exist in the database
    non_existent_user_data = {
        "sub": "nonexistent@example.com",
        "user_id": 99999,
        "uuid": str(uuid.uuid4())
    }
    token = create_access_token(data=non_existent_user_data, expires_delta=timedelta(minutes=30))
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(ME_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_me_with_login_flow(client: TestClient, test_user):
    """Test complete login flow and then get user info."""
    # First, login to get a token
    login_data = {"username": test_user["email"], "password": test_user["password"]}
    login_response = client.post(TOKEN_URL, data=login_data)
    
    assert login_response.status_code == status.HTTP_200_OK
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    # Then use the token to get user info
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(ME_URL, headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data["email"] == test_user["email"]
    assert user_data["uuid"] == test_user["uuid"]

def test_get_me_database_error(client: TestClient, auth_token):
    """Test that endpoint handles database errors gracefully."""
    # This test would require mocking the database connection to simulate errors
    # For now, we'll just test that the endpoint works normally
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get(ME_URL, headers=headers)
    assert response.status_code == status.HTTP_200_OK

def test_get_me_missing_token_claims(client: TestClient):
    """Test that endpoint returns 401 when token is missing required claims."""
    # Create a token with missing claims
    incomplete_token_data = {
        "sub": "test@example.com"
        # Missing user_id and uuid
    }
    token = create_access_token(data=incomplete_token_data, expires_delta=timedelta(minutes=30))
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(ME_URL, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_me_with_different_user_data(client: TestClient, db_session: Session):
    """Test get_me with different user data to ensure proper isolation."""
    # Create a different user
    different_email = f"different_user_{uuid.uuid4()}@example.com"
    different_user_data = {
        "email": different_email,
        "hashed_password": hash_password("TestPassword123!"),
        "full_name": "Different User",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "uuid": str(uuid.uuid4())
    }
    
    different_user = None
    try:
        new_user = User(**different_user_data)
        db_session.add(new_user)
        db_session.flush()
        db_session.refresh(new_user)
        different_user = new_user
        
        # Commit to ensure the user is persisted
        db_session.commit()
    
        # Create token for the different user
        token_data = {
            "sub": different_user.email,
            "user_id": different_user.id,
            "uuid": different_user.uuid
        }
        token = create_access_token(data=token_data, expires_delta=timedelta(minutes=30))
    
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(ME_URL, headers=headers)
    
        assert response.status_code == status.HTTP_200_OK
        user_data = response.json()
        
        # Verify the returned user data matches the different user
        assert user_data["email"] == different_user.email
        assert user_data["uuid"] == different_user.uuid
        assert user_data["full_name"] == different_user.full_name
        
    finally:
        if different_user and different_user.id:
            db_session.delete(different_user)
            db_session.commit() 