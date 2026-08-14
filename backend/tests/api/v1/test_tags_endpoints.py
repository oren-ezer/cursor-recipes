import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import status
from fastapi.testclient import TestClient

from src.main import app
from src.utils.dependencies import get_tag_service, get_recipe_service_with_tags, get_current_user

TAGS_URL = "/api/v1/tags"

@pytest.fixture
def mock_tag_service():
    return MagicMock()

@pytest.fixture
def mock_recipe_service():
    return MagicMock()

@pytest.fixture
def client_with_mocks(mock_tag_service, mock_recipe_service):
    app.dependency_overrides[get_tag_service] = lambda: mock_tag_service
    app.dependency_overrides[get_recipe_service_with_tags] = lambda: mock_recipe_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def mock_auth():
    with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock:
        mock.return_value = {"uuid": "test-uuid", "email": "test@test.com", "is_superuser": False}
        yield mock

@pytest.fixture
def override_current_user():
    user = {"uuid": "test-uuid", "email": "test@test.com", "is_superuser": False}
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def override_superuser():
    user = {"uuid": "admin-uuid", "email": "admin@test.com", "is_superuser": True}
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_user, None)

def test_get_all_tags_success(client_with_mocks, mock_tag_service):
    mock_tag_service.get_tags_with_category_info.return_value = {
        "tags": [], "grouped_tags": {}, "total": 0, "limit": 100, "offset": 0
    }
    response = client_with_mocks.get(f"{TAGS_URL}/")
    assert response.status_code == status.HTTP_200_OK
    mock_tag_service.get_tags_with_category_info.assert_called_once_with(limit=100, offset=0)

def test_get_all_tags_exception(client_with_mocks, mock_tag_service):
    mock_tag_service.get_tags_with_category_info.side_effect = Exception("DB error")
    response = client_with_mocks.get(f"{TAGS_URL}/")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

def test_get_tags_grouped_by_category_success(client_with_mocks, mock_tag_service):
    mock_tag_service.get_tags_by_category.return_value = {"DIET": []}
    response = client_with_mocks.get(f"{TAGS_URL}/grouped")
    assert response.status_code == status.HTTP_200_OK
    mock_tag_service.get_tags_by_category.assert_called_once_with(limit=100, offset=0)

def test_get_tags_grouped_by_category_exception(client_with_mocks, mock_tag_service):
    mock_tag_service.get_tags_by_category.side_effect = Exception("DB error")
    response = client_with_mocks.get(f"{TAGS_URL}/grouped")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

def test_search_tags_success(client_with_mocks, mock_tag_service):
    mock_tag_service.search_tags.return_value = {"tags": [], "total": 0, "limit": 100, "offset": 0}
    response = client_with_mocks.get(f"{TAGS_URL}/search?name=test")
    assert response.status_code == status.HTTP_200_OK
    mock_tag_service.search_tags.assert_called_once_with(name="test", limit=100, offset=0)

def test_search_tags_exception(client_with_mocks, mock_tag_service):
    mock_tag_service.search_tags.side_effect = Exception("DB error")
    response = client_with_mocks.get(f"{TAGS_URL}/search")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

def test_get_popular_tags_success(client_with_mocks, mock_tag_service):
    mock_tag_service.get_popular_tags.return_value = []
    response = client_with_mocks.get(f"{TAGS_URL}/popular")
    assert response.status_code == status.HTTP_200_OK
    mock_tag_service.get_popular_tags.assert_called_once_with(limit=10)

def test_get_popular_tags_exception(client_with_mocks, mock_tag_service):
    mock_tag_service.get_popular_tags.side_effect = Exception("DB error")
    response = client_with_mocks.get(f"{TAGS_URL}/popular")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

def test_get_tags_for_recipe_not_found(client_with_mocks, mock_recipe_service):
    mock_recipe_service.get_recipe.return_value = None
    response = client_with_mocks.get(f"{TAGS_URL}/recipes/1/tags")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_tags_for_recipe_public(client_with_mocks, mock_recipe_service, mock_tag_service):
    mock_recipe_service.get_recipe.return_value.is_public = True
    mock_tag_service.get_tags_for_recipe.return_value = []
    
    response = client_with_mocks.get(f"{TAGS_URL}/recipes/1/tags")
    assert response.status_code == status.HTTP_200_OK
    mock_tag_service.get_tags_for_recipe.assert_called_once_with(1)

def test_get_tags_for_recipe_private_unauth(client_with_mocks, mock_recipe_service):
    mock_recipe_service.get_recipe.return_value.is_public = False
    
    response = client_with_mocks.get(f"{TAGS_URL}/recipes/1/tags")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_tags_for_recipe_private_forbidden(client_with_mocks, mock_recipe_service, mock_auth):
    mock_recipe_service.get_recipe.return_value.is_public = False
    mock_recipe_service.get_recipe.return_value.user_id = "other-uuid"
    
    response = client_with_mocks.get(f"{TAGS_URL}/recipes/1/tags", headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_get_tags_for_recipe_private_owner(client_with_mocks, mock_recipe_service, mock_tag_service, mock_auth):
    mock_recipe_service.get_recipe.return_value.is_public = False
    mock_recipe_service.get_recipe.return_value.user_id = "test-uuid"
    mock_tag_service.get_tags_for_recipe.return_value = []
    
    response = client_with_mocks.get(f"{TAGS_URL}/recipes/1/tags", headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_200_OK
    mock_tag_service.get_tags_for_recipe.assert_called_once_with(1)

def test_get_tags_for_recipe_private_superuser(client_with_mocks, mock_recipe_service, mock_tag_service, mock_auth):
    mock_recipe_service.get_recipe.return_value.is_public = False
    mock_recipe_service.get_recipe.return_value.user_id = "other-uuid"
    
    with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth_admin:
        mock_auth_admin.return_value = {"uuid": "admin-uuid", "email": "admin@test.com", "is_superuser": True}
        response = client_with_mocks.get(f"{TAGS_URL}/recipes/1/tags", headers={"Authorization": "Bearer fake"})
        assert response.status_code == status.HTTP_200_OK
        mock_tag_service.get_tags_for_recipe.assert_called_once_with(1)

def test_get_tags_for_recipe_exception(client_with_mocks, mock_recipe_service, mock_tag_service):
    mock_recipe_service.get_recipe.return_value.is_public = True
    mock_tag_service.get_tags_for_recipe.side_effect = Exception("DB error")
    
    response = client_with_mocks.get(f"{TAGS_URL}/recipes/1/tags")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

def test_update_recipe_tags_not_found(client_with_mocks, mock_recipe_service, override_current_user):
    mock_recipe_service.get_recipe.return_value = None
    response = client_with_mocks.put(f"{TAGS_URL}/recipes/1/tags", json={"add_tag_ids": [1]})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_recipe_tags_forbidden(client_with_mocks, mock_recipe_service, override_current_user):
    mock_recipe_service.get_recipe.return_value.user_id = "other-uuid"
    response = client_with_mocks.put(f"{TAGS_URL}/recipes/1/tags", json={"add_tag_ids": [1]})
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_update_recipe_tags_owner_success(client_with_mocks, mock_recipe_service, mock_tag_service, override_current_user):
    mock_recipe_service.get_recipe.return_value.user_id = "test-uuid"
    mock_tag_service.update_recipe_tags.return_value = {
        "added_tags": [], "removed_tags": [], "current_tags": [], "warnings": [], "errors": []
    }
    
    response = client_with_mocks.put(f"{TAGS_URL}/recipes/1/tags", json={"add_tag_ids": [1], "remove_tag_ids": [2]})
    assert response.status_code == status.HTTP_200_OK
    mock_tag_service.update_recipe_tags.assert_called_once_with(recipe_id=1, add_tag_ids=[1], remove_tag_ids=[2])

def test_update_recipe_tags_superuser_success(client_with_mocks, mock_recipe_service, mock_tag_service, override_superuser):
    mock_recipe_service.get_recipe.return_value.user_id = "other-uuid"
    mock_tag_service.update_recipe_tags.return_value = {
        "added_tags": [], "removed_tags": [], "current_tags": [], "warnings": [], "errors": []
    }
    
    response = client_with_mocks.put(f"{TAGS_URL}/recipes/1/tags", json={"add_tag_ids": [1]})
    assert response.status_code == status.HTTP_200_OK
    mock_tag_service.update_recipe_tags.assert_called_once_with(recipe_id=1, add_tag_ids=[1], remove_tag_ids=None)

def test_update_recipe_tags_value_error(client_with_mocks, mock_recipe_service, mock_tag_service, override_current_user):
    mock_recipe_service.get_recipe.return_value.user_id = "test-uuid"
    mock_tag_service.update_recipe_tags.side_effect = ValueError("Invalid tag")
    
    response = client_with_mocks.put(f"{TAGS_URL}/recipes/1/tags", json={"add_tag_ids": [1]})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid tag"

def test_update_recipe_tags_exception(client_with_mocks, mock_recipe_service, mock_tag_service, override_current_user):
    mock_recipe_service.get_recipe.return_value.user_id = "test-uuid"
    mock_tag_service.update_recipe_tags.side_effect = Exception("DB error")
    
    response = client_with_mocks.put(f"{TAGS_URL}/recipes/1/tags", json={"add_tag_ids": [1]})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
