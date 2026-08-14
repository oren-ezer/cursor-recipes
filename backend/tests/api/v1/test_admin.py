import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime, timezone

from src.main import app
from src.utils.dependencies import get_recipe_service_with_tags, get_tag_service, get_app_settings_service, get_database_session
from src.models.tag import TagCategory

@pytest.fixture
def mock_recipe_service():
    return MagicMock()

@pytest.fixture
def mock_tag_service():
    return MagicMock()

@pytest.fixture
def mock_app_settings_service():
    return MagicMock()

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def mock_get_current_user():
    with patch("src.utils.dependencies._get_current_user_from_token", new_callable=AsyncMock) as mock:
        yield mock

@pytest.fixture
def client(mock_recipe_service, mock_tag_service, mock_app_settings_service, mock_db_session):
    app.dependency_overrides[get_recipe_service_with_tags] = lambda: mock_recipe_service
    app.dependency_overrides[get_tag_service] = lambda: mock_tag_service
    app.dependency_overrides[get_app_settings_service] = lambda: mock_app_settings_service
    app.dependency_overrides[get_database_session] = lambda: mock_db_session
    
    with TestClient(app) as c:
        yield c
        
    app.dependency_overrides.clear()

# Helpers
def assert_unauthorized(client, method, url, **kwargs):
    response = getattr(client, method)(url, **kwargs)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def assert_forbidden(client, method, url, mock_get_current_user, **kwargs):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    response = getattr(client, method)(url, headers={"Authorization": "Bearer fake_token"}, **kwargs)
    assert response.status_code == 403
    assert response.json()["detail"] == "Administrator access required"

def setup_admin(mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "admin-uuid", "is_superuser": True}
    return {"Authorization": "Bearer fake_token"}

# App Settings
def test_get_app_settings_auth(client, mock_get_current_user):
    assert_unauthorized(client, "get", "/api/v1/admins/settings")
    assert_forbidden(client, "get", "/api/v1/admins/settings", mock_get_current_user)

def test_get_app_settings_success(client, mock_app_settings_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_app_settings_service.get_grouped_settings.return_value = {"group1": {"setting1": "val1"}}
    
    response = client.get("/api/v1/admins/settings", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"group1": {"setting1": "val1"}}

def test_update_app_settings_auth(client, mock_get_current_user):
    assert_unauthorized(client, "put", "/api/v1/admins/settings", json={"settings": {"key": "val"}})
    assert_forbidden(client, "put", "/api/v1/admins/settings", mock_get_current_user, json={"settings": {"key": "val"}})

def test_update_app_settings_success(client, mock_app_settings_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_app_settings_service.update_settings.return_value = {"key": "val"}
    
    response = client.put("/api/v1/admins/settings", json={"settings": {"key": "val"}}, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"key": "val"}

def test_update_app_settings_value_error(client, mock_app_settings_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_app_settings_service.update_settings.side_effect = ValueError("Invalid setting")
    
    response = client.put("/api/v1/admins/settings", json={"settings": {"key": "val"}}, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid setting"

def test_test_config_success(client, mock_app_settings_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_app_settings_service.get_image_upload_limits.return_value = {"max_file_size_mb": 5, "max_files_per_upload": 10}
    mock_app_settings_service.get_integration_status.return_value = {"openai": True}
    mock_app_settings_service.get_str.return_value = "local"
    
    response = client.get("/api/v1/admins/config-test", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["openai"] == True
    assert data["max_image_upload_size_mb"] == 5
    assert data["max_images_per_upload"] == 10
    assert data["image_storage_backend"] == "local"

def test_test_setup_success(client, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    response = client.get("/api/v1/admins/test-setup", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["details"]["sqlmodel_imported"] == True

def test_test_setup_error(client, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    
    with patch.dict('sys.modules', {'sqlmodel': None}):
        response = client.get("/api/v1/admins/test-setup", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "error"

def test_test_db_connection_success(client, mock_db_session, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_db_session.execute.return_value = None
    
    response = client.get("/api/v1/admins/test-db-connection", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_test_db_connection_error(client, mock_db_session, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_db_session.execute.side_effect = Exception("Connection failed")
    
    response = client.get("/api/v1/admins/test-db-connection", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "error"

# Recipes
def test_get_all_recipes_success(client, mock_recipe_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_recipe_service.get_all_recipes_with_tags.return_value = {
        "recipes": [
            {
                "id": 1,
                "uuid": "test-uuid-1",
                "title": "Recipe",
                "description": "Desc",
                "ingredients": [],
                "instructions": [],
                "preparation_time": 10,
                "cooking_time": 20,
                "servings": 2,
                "difficulty_level": "Easy",
                "user_id": "owner-uuid",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_public": True,
                "tags": []
            }
        ],
        "total": 1,
        "limit": 1000,
        "offset": 0
    }
    
    response = client.get("/api/v1/admins/recipes/", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1

def test_get_all_recipes_exception(client, mock_recipe_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_recipe_service.get_all_recipes_with_tags.side_effect = Exception("DB error")
    
    response = client.get("/api/v1/admins/recipes/", headers=headers)
    assert response.status_code == 500

# Tags
def get_mock_tag():
    return {
        "id": 1,
        "uuid": "tag-uuid",
        "name": "Tag Name",
        "recipe_counter": 0,
        "category": "Cuisine Types",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

def test_get_tag_success(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.get_tag.return_value = get_mock_tag()
    
    response = client.get("/api/v1/admins/tags/1", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Tag Name"

def test_get_tag_not_found(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.get_tag.return_value = None
    
    response = client.get("/api/v1/admins/tags/1", headers=headers)
    assert response.status_code == 404

def test_get_tag_exception(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.get_tag.side_effect = Exception("DB error")
    
    response = client.get("/api/v1/admins/tags/1", headers=headers)
    assert response.status_code == 500

def test_get_tag_by_uuid_success(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.get_tag_by_uuid.return_value = get_mock_tag()
    
    response = client.get("/api/v1/admins/tags/uuid/tag-uuid", headers=headers)
    assert response.status_code == 200

def test_get_tag_by_uuid_not_found(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.get_tag_by_uuid.return_value = None
    
    response = client.get("/api/v1/admins/tags/uuid/tag-uuid", headers=headers)
    assert response.status_code == 404

def test_get_tag_by_uuid_exception(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.get_tag_by_uuid.side_effect = Exception("DB error")
    
    response = client.get("/api/v1/admins/tags/uuid/tag-uuid", headers=headers)
    assert response.status_code == 500

def test_get_tag_by_name_success(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.get_tag_by_name.return_value = get_mock_tag()
    
    response = client.get("/api/v1/admins/tags/name/tag_name", headers=headers)
    assert response.status_code == 200

def test_get_tag_by_name_not_found(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.get_tag_by_name.return_value = None
    
    response = client.get("/api/v1/admins/tags/name/tag_name", headers=headers)
    assert response.status_code == 404

def test_get_tag_by_name_exception(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.get_tag_by_name.side_effect = Exception("DB error")
    
    response = client.get("/api/v1/admins/tags/name/tag_name", headers=headers)
    assert response.status_code == 500

def test_create_tag_success(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.create_tag.return_value = get_mock_tag()
    
    response = client.post("/api/v1/admins/tags/", json={"name": "Tag Name", "category": "Cuisine Types"}, headers=headers)
    assert response.status_code == 201

def test_create_tag_invalid_category(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    
    response = client.post("/api/v1/admins/tags/", json={"name": "Tag Name", "category": "InvalidCat"}, headers=headers)
    assert response.status_code == 400
    assert "Invalid category" in response.json()["detail"]

def test_create_tag_value_error(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.create_tag.side_effect = ValueError("Tag already exists")
    
    response = client.post("/api/v1/admins/tags/", json={"name": "Tag Name", "category": "Cuisine Types"}, headers=headers)
    assert response.status_code == 400

def test_create_tag_exception(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.create_tag.side_effect = Exception("DB Error")
    
    response = client.post("/api/v1/admins/tags/", json={"name": "Tag Name", "category": "Cuisine Types"}, headers=headers)
    assert response.status_code == 500

def test_update_tag_success(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.update_tag.return_value = get_mock_tag()
    
    response = client.put("/api/v1/admins/tags/1", json={"name": "Tag Name", "category": "Cuisine Types"}, headers=headers)
    assert response.status_code == 200

def test_update_tag_invalid_category(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    
    response = client.put("/api/v1/admins/tags/1", json={"name": "Tag Name", "category": "InvalidCat"}, headers=headers)
    assert response.status_code == 400

def test_update_tag_not_found(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.update_tag.side_effect = ValueError("Tag not found")
    
    response = client.put("/api/v1/admins/tags/1", json={"name": "Tag Name", "category": "Cuisine Types"}, headers=headers)
    assert response.status_code == 404

def test_update_tag_other_value_error(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.update_tag.side_effect = ValueError("Other error")
    
    response = client.put("/api/v1/admins/tags/1", json={"name": "Tag Name", "category": "Cuisine Types"}, headers=headers)
    assert response.status_code == 400

def test_update_tag_exception(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.update_tag.side_effect = Exception("DB Error")
    
    response = client.put("/api/v1/admins/tags/1", json={"name": "Tag Name", "category": "Cuisine Types"}, headers=headers)
    assert response.status_code == 500

def test_delete_tag_success(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.delete_tag.return_value = {"tag_name": "Tag Name", "recipes_affected": 0}
    
    response = client.delete("/api/v1/admins/tags/1", headers=headers)
    assert response.status_code == 200
    assert response.json()["tag_name"] == "Tag Name"

def test_delete_tag_not_found(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.delete_tag.side_effect = ValueError("Tag not found")
    
    response = client.delete("/api/v1/admins/tags/1", headers=headers)
    assert response.status_code == 404

def test_delete_tag_other_value_error(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.delete_tag.side_effect = ValueError("Other error")
    
    response = client.delete("/api/v1/admins/tags/1", headers=headers)
    assert response.status_code == 400

def test_delete_tag_exception(client, mock_tag_service, mock_get_current_user):
    headers = setup_admin(mock_get_current_user)
    mock_tag_service.delete_tag.side_effect = Exception("DB Error")
    
    response = client.delete("/api/v1/admins/tags/1", headers=headers)
    assert response.status_code == 500