import pytest
from unittest.mock import MagicMock
from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import uuid

from src.main import app
from src.utils.dependencies import get_user_service, get_current_user
from src.api.v1.endpoints.users import get_admin_user, UserCreate, UserUpdate

@pytest.fixture
def mock_user_service():
    return MagicMock()

@pytest.fixture
def mock_current_user():
    return {
        "id": 1,
        "uuid": str(uuid.uuid4()),
        "email": "user@example.com",
        "full_name": "Normal User",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

@pytest.fixture
def mock_admin_user():
    return {
        "id": 2,
        "uuid": str(uuid.uuid4()),
        "email": "admin@example.com",
        "full_name": "Admin User",
        "is_active": True,
        "is_superuser": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

@pytest.fixture
def client(mock_user_service, mock_current_user):
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    with TestClient(app) as c:
        yield c
        
    app.dependency_overrides.clear()

def test_user_create_sanitize_none():
    user = UserCreate(email="test@example.com", password="Password123!", full_name=None)
    assert user.full_name is None

def test_user_update_sanitize_none():
    user = UserUpdate(full_name=None)
    assert user.full_name is None

def test_get_admin_user_success():
    admin_user = {"is_superuser": True}
    assert get_admin_user(admin_user) == admin_user

def test_get_admin_user_forbidden():
    from fastapi import HTTPException
    normal_user = {"is_superuser": False}
    with pytest.raises(HTTPException) as exc:
        get_admin_user(normal_user)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc.value.detail == "Administrator access required"

def test_search_users_success(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    
    mock_user_service.search_for_users.return_value = {
        "users": [mock_admin_user],
        "total": 1,
        "limit": 100,
        "offset": 0
    }
    
    response = client.get("/api/v1/users/search?email=admin")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == 1
    mock_user_service.search_for_users.assert_called_once_with(
        email="admin",
        full_name=None,
        is_active=None,
        limit=100,
        offset=0
    )

def test_search_users_exception(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.search_for_users.side_effect = Exception("DB error")
    
    response = client.get("/api/v1/users/search")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Failed to search users"

def test_search_users_http_exception(client, mock_user_service, mock_admin_user):
    from fastapi import HTTPException
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.search_for_users.side_effect = HTTPException(status_code=400, detail="Bad request")
    
    response = client.get("/api/v1/users/search")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_get_users_success(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    
    mock_user_service.get_all_users.return_value = {
        "users": [mock_admin_user],
        "total": 1,
        "limit": 100,
        "offset": 0
    }
    
    response = client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == 1
    mock_user_service.get_all_users.assert_called_once_with(limit=100, offset=0)

def test_get_users_exception(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.get_all_users.side_effect = Exception("DB error")
    
    response = client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

def test_get_users_http_exception(client, mock_user_service, mock_admin_user):
    from fastapi import HTTPException
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.get_all_users.side_effect = HTTPException(status_code=400, detail="Bad request")
    
    response = client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_read_users_me_success(client, mock_user_service, mock_current_user):
    from src.api.v1.endpoints.users import read_users_me
    import asyncio
    
    mock_request = MagicMock()
    mock_request.state.user = mock_current_user
    mock_user_service.get_current_user.return_value = mock_current_user
    
    result = asyncio.run(read_users_me(mock_request, mock_user_service))
    assert result == mock_current_user
    mock_user_service.get_current_user.assert_called_once_with(mock_current_user["uuid"])

def test_read_users_me_not_authenticated(mock_user_service):
    from src.api.v1.endpoints.users import read_users_me
    from fastapi import HTTPException
    import asyncio
    
    mock_request = MagicMock()
    mock_request.state.user = None
    
    with pytest.raises(HTTPException) as exc:
        asyncio.run(read_users_me(mock_request, mock_user_service))
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Not authenticated"

def test_read_users_me_not_found(mock_user_service, mock_current_user):
    from src.api.v1.endpoints.users import read_users_me
    from fastapi import HTTPException
    import asyncio
    
    mock_request = MagicMock()
    mock_request.state.user = mock_current_user
    mock_user_service.get_current_user.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        asyncio.run(read_users_me(mock_request, mock_user_service))
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "User not found"

def test_read_users_me_exception(mock_user_service, mock_current_user):
    from src.api.v1.endpoints.users import read_users_me
    from fastapi import HTTPException
    import asyncio
    
    mock_request = MagicMock()
    mock_request.state.user = mock_current_user
    mock_user_service.get_current_user.side_effect = Exception("DB error")
    
    with pytest.raises(HTTPException) as exc:
        asyncio.run(read_users_me(mock_request, mock_user_service))
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.value.detail == "Failed to retrieve user information"

def test_get_user_success(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    
    mock_user_service.get_user.return_value = mock_admin_user
    
    response = client.get("/api/v1/users/2")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == 2
    mock_user_service.get_user.assert_called_once_with(2)

def test_get_user_not_found(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    
    mock_user_service.get_user.return_value = None
    
    response = client.get("/api/v1/users/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_user_exception(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.get_user.side_effect = Exception("DB error")
    
    response = client.get("/api/v1/users/2")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

def test_get_user_http_exception(client, mock_user_service, mock_admin_user):
    from fastapi import HTTPException
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.get_user.side_effect = HTTPException(status_code=400, detail="Bad request")
    
    response = client.get("/api/v1/users/2")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_register_user_success(client, mock_user_service):
    mock_user_service.create_user.return_value = {
        "id": 3,
        "uuid": str(uuid.uuid4()),
        "email": "new@example.com",
        "full_name": "New User",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    response = client.post("/api/v1/users/register", json={
        "email": "new@example.com",
        "password": "Password123!",
        "full_name": "New User"
    })
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["email"] == "new@example.com"
    mock_user_service.create_user.assert_called_once_with(
        email="new@example.com",
        password="Password123!",
        full_name="New User"
    )

def test_register_user_value_error(client, mock_user_service):
    mock_user_service.create_user.side_effect = ValueError("Email already exists")
    
    response = client.post("/api/v1/users/register", json={
        "email": "new@example.com",
        "password": "Password123!"
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Email already exists"

def test_register_user_exception(client, mock_user_service):
    mock_user_service.create_user.side_effect = Exception("DB error")
    
    response = client.post("/api/v1/users/register", json={
        "email": "new@example.com",
        "password": "Password123!"
    })
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

def test_update_user_success_self(client, mock_user_service, mock_current_user):
    mock_user_service.update_user.return_value = mock_current_user
    
    response = client.put("/api/v1/users/1", json={"full_name": "Updated Name"})
    assert response.status_code == status.HTTP_200_OK
    mock_user_service.update_user.assert_called_once_with(1, {"full_name": "Updated Name"})

def test_update_user_success_admin(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    mock_user_service.update_user.return_value = mock_admin_user
    
    response = client.put("/api/v1/users/1", json={"full_name": "Updated Name"})
    assert response.status_code == status.HTTP_200_OK

def test_update_user_forbidden(client, mock_user_service):
    response = client.put("/api/v1/users/2", json={"full_name": "Updated Name"})
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_update_user_empty_data(client, mock_user_service, mock_current_user):
    mock_user_service.get_user.return_value = mock_current_user
    
    response = client.put("/api/v1/users/1", json={})
    assert response.status_code == status.HTTP_200_OK
    mock_user_service.get_user.assert_called_once_with(1)
    mock_user_service.update_user.assert_not_called()

def test_update_user_empty_data_not_found(client, mock_user_service):
    mock_user_service.get_user.return_value = None
    
    response = client.put("/api/v1/users/1", json={})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_user_value_error_not_found(client, mock_user_service):
    mock_user_service.update_user.side_effect = ValueError("User not found")
    
    response = client.put("/api/v1/users/1", json={"full_name": "Updated Name"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_user_value_error_email_taken(client, mock_user_service):
    mock_user_service.update_user.side_effect = ValueError("Email already taken")
    
    response = client.put("/api/v1/users/1", json={"email": "taken@example.com"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_update_user_value_error_other(client, mock_user_service):
    mock_user_service.update_user.side_effect = ValueError("Invalid data")
    
    response = client.put("/api/v1/users/1", json={"full_name": "Updated Name"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_update_user_http_exception(client, mock_user_service):
    from fastapi import HTTPException
    mock_user_service.update_user.side_effect = HTTPException(status_code=400, detail="Bad request")
    
    response = client.put("/api/v1/users/1", json={"full_name": "Updated Name"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_update_user_exception(client, mock_user_service):
    mock_user_service.update_user.side_effect = Exception("DB error")
    
    response = client.put("/api/v1/users/1", json={"full_name": "Updated Name"})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

def test_delete_user_success_self(client, mock_user_service):
    response = client.delete("/api/v1/users/1")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_user_service.delete_user.assert_called_once_with(1, None)

def test_delete_user_success_admin(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    response = client.delete("/api/v1/users/1")
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_delete_user_forbidden(client, mock_user_service):
    response = client.delete("/api/v1/users/2")
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_delete_user_value_error_not_found(client, mock_user_service):
    mock_user_service.delete_user.side_effect = ValueError("User not found")
    response = client.delete("/api/v1/users/1")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_user_value_error_owns_recipes(client, mock_user_service):
    mock_user_service.delete_user.side_effect = ValueError("User owns recipes")
    response = client.delete("/api/v1/users/1")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_delete_user_value_error_invalid_admin(client, mock_user_service):
    mock_user_service.delete_user.side_effect = ValueError("Invalid admin user")
    response = client.delete("/api/v1/users/1")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_delete_user_value_error_other(client, mock_user_service):
    mock_user_service.delete_user.side_effect = ValueError("Other error")
    response = client.delete("/api/v1/users/1")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_delete_user_http_exception(client, mock_user_service):
    from fastapi import HTTPException
    mock_user_service.delete_user.side_effect = HTTPException(status_code=400, detail="Bad request")
    response = client.delete("/api/v1/users/1")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_delete_user_exception(client, mock_user_service):
    mock_user_service.delete_user.side_effect = Exception("DB error")
    response = client.delete("/api/v1/users/1")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

def test_set_superuser_status_success(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.set_superuser_status.return_value = mock_admin_user
    
    response = client.put("/api/v1/users/2/set-superuser", json={"is_superuser": True})
    assert response.status_code == status.HTTP_200_OK
    mock_user_service.set_superuser_status.assert_called_once_with(2, True)

def test_set_superuser_status_value_error_not_found(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.set_superuser_status.side_effect = ValueError("User not found")
    
    response = client.put("/api/v1/users/2/set-superuser", json={"is_superuser": True})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_set_superuser_status_value_error_other(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.set_superuser_status.side_effect = ValueError("Other error")
    
    response = client.put("/api/v1/users/2/set-superuser", json={"is_superuser": True})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_set_superuser_status_http_exception(client, mock_user_service, mock_admin_user):
    from fastapi import HTTPException
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.set_superuser_status.side_effect = HTTPException(status_code=400, detail="Bad request")
    
    response = client.put("/api/v1/users/2/set-superuser", json={"is_superuser": True})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_set_superuser_status_exception(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.set_superuser_status.side_effect = Exception("DB error")
    
    response = client.put("/api/v1/users/2/set-superuser", json={"is_superuser": True})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

def test_reset_password_success(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.reset_password_by_admin.return_value = "TempPass123!"
    
    response = client.post("/api/v1/users/2/reset-password")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["temporary_password"] == "TempPass123!"
    mock_user_service.reset_password_by_admin.assert_called_once_with(admin_id=mock_admin_user["id"], target_user_id=2)

def test_reset_password_not_found(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.reset_password_by_admin.side_effect = ValueError("Target user not found")
    
    response = client.post("/api/v1/users/2/reset-password")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_reset_password_value_error_other(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.reset_password_by_admin.side_effect = ValueError("Other error")
    
    response = client.post("/api/v1/users/2/reset-password")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_reset_password_exception(client, mock_user_service, mock_admin_user):
    app.dependency_overrides[get_admin_user] = lambda: mock_admin_user
    mock_user_service.reset_password_by_admin.side_effect = Exception("DB Error")
    
    response = client.post("/api/v1/users/2/reset-password")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

def test_change_password_success(client, mock_user_service, mock_current_user):
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    mock_user_service.change_password.return_value = None
    
    response = client.post("/api/v1/users/me/change-password", json={
        "current_password": "OldPassword123!",
        "new_password": "NewPassword123!"
    })
    
    assert response.status_code == status.HTTP_200_OK
    mock_user_service.change_password.assert_called_once_with(
        user_uuid=mock_current_user["uuid"],
        current_password="OldPassword123!",
        new_password="NewPassword123!"
    )

def test_change_password_value_error(client, mock_user_service, mock_current_user):
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    mock_user_service.change_password.side_effect = ValueError("Invalid current password")
    
    response = client.post("/api/v1/users/me/change-password", json={
        "current_password": "WrongPassword123!",
        "new_password": "NewPassword123!"
    })
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_change_password_exception(client, mock_user_service, mock_current_user):
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    mock_user_service.change_password.side_effect = Exception("DB Error")
    
    response = client.post("/api/v1/users/me/change-password", json={
        "current_password": "OldPassword123!",
        "new_password": "NewPassword123!"
    })
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

def test_login_for_access_token_success(client, mock_user_service):
    mock_user_service.login_for_access_token.return_value = {
        "access_token": "token123",
        "token_type": "bearer"
    }
    
    response = client.post("/api/v1/users/token", data={
        "username": "user@example.com",
        "password": "Password123!"
    })
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["access_token"] == "token123"
    mock_user_service.login_for_access_token.assert_called_once_with(
        username="user@example.com",
        password="Password123!"
    )

def test_login_for_access_token_incorrect_credentials(client, mock_user_service):
    mock_user_service.login_for_access_token.side_effect = ValueError("Incorrect email or password")
    
    response = client.post("/api/v1/users/token", data={
        "username": "user@example.com",
        "password": "WrongPassword!"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Incorrect email or password"

def test_login_for_access_token_inactive_user(client, mock_user_service):
    mock_user_service.login_for_access_token.side_effect = ValueError("Inactive user")
    
    response = client.post("/api/v1/users/token", data={
        "username": "user@example.com",
        "password": "Password123!"
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Inactive user"

def test_login_for_access_token_value_error_other(client, mock_user_service):
    mock_user_service.login_for_access_token.side_effect = ValueError("Other error")
    
    response = client.post("/api/v1/users/token", data={
        "username": "user@example.com",
        "password": "Password123!"
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_login_for_access_token_exception(client, mock_user_service):
    mock_user_service.login_for_access_token.side_effect = Exception("DB error")
    
    response = client.post("/api/v1/users/token", data={
        "username": "user@example.com",
        "password": "Password123!"
    })
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
