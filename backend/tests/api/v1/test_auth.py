import pytest
import uuid
from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlmodel import Session as SQLModelSession

from src.core.config import settings
from src.core.security import hash_password
from src.utils.database_session import engine
from src.models.user import User

# This assumes that your .env file is loaded correctly when pytest runs,
# or you have pytest-dotenv configured.

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
    Yields a dictionary with user details (email, password, id, is_active).
    """
    test_email = f"test_user_{uuid.uuid4()}@example.com"
    test_password = "TestPassword123!"
    hashed_password = hash_password(test_password)
    current_time = datetime.now(timezone.utc)

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
            "is_active": True
        }
    finally:
        if created_user and created_user.id:
            # Clean up using SQLAlchemy
            db_session.delete(created_user)
            db_session.commit()

@pytest.fixture
def inactive_test_user(db_session: Session):
    """
    Creates an inactive user in the database for testing and cleans up afterwards.
    Yields a dictionary with user details (email, password, id, is_active).
    """
    test_email = f"inactive_user_{uuid.uuid4()}@example.com"
    test_password = "TestPassword123!"
    hashed_password = hash_password(test_password)
    current_time = datetime.now(timezone.utc)
    
    user_data = {
        "email": test_email,
        "hashed_password": hashed_password,
        "full_name": "Inactive Test User",
        "is_active": False,
        "is_superuser": False,
        "created_at": current_time,
        "updated_at": current_time,
        "uuid": str(uuid.uuid4())
    }
    
    created_user = None
    try:
        # Create user using SQLAlchemy
        new_user = User(**user_data)
        db_session.add(new_user)
        db_session.flush()
        db_session.refresh(new_user)
        created_user = new_user
        
        yield {
            "id": created_user.id,
            "email": test_email,
            "password": test_password,
            "is_active": False
        }
    finally:
        if created_user and created_user.id:
            # Clean up using SQLAlchemy
            db_session.delete(created_user)
            db_session.flush()

def test_login_success(client: TestClient, test_user):
    """Test successful login with correct credentials."""
    # Debug: Check if user exists
    print(f"Test user created: {test_user}")
    print(f"User ID: {test_user['id']}")
    print(f"User email: {test_user['email']}")
    print(f"User password: {test_user['password']}")
    
    login_data = {"username": test_user["email"], "password": test_user["password"]}
    print(f"Login data: {login_data}")
    
    response = client.post(TOKEN_URL, data=login_data)
    
    # Debug output
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient, test_user):
    """Test login with incorrect password."""
    login_data = {"username": test_user["email"], "password": "wrongpassword"}
    response = client.post(TOKEN_URL, data=login_data)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_login_non_existent_user(client: TestClient):
    """Test login with non-existent user."""
    login_data = {"username": "nonexistent@example.com", "password": "TestPassword123!"}
    response = client.post(TOKEN_URL, data=login_data)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_login_inactive_user(client: TestClient, inactive_test_user):
    """Test login with inactive user."""
    login_data = {"username": inactive_test_user["email"], "password": inactive_test_user["password"]}
    response = client.post(TOKEN_URL, data=login_data)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 