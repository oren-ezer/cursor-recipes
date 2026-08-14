import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from src.main import app
from src.utils.dependencies import get_interaction_service

INTERACTIONS_URL = "/api/v1/recipes"

@pytest.fixture
def mock_interaction_service():
    return MagicMock()

@pytest.fixture
def client_with_mocks(mock_interaction_service):
    app.dependency_overrides[get_interaction_service] = lambda: mock_interaction_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def mock_auth():
    with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock:
        mock.return_value = {"uuid": "test-uuid", "email": "test@test.com", "is_superuser": False}
        yield mock

@pytest.fixture
def mock_auth_superuser():
    with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock:
        mock.return_value = {"uuid": "admin-uuid", "email": "admin@test.com", "is_superuser": True}
        yield mock

def test_toggle_favorite_unauthorized(client_with_mocks):
    response = client_with_mocks.post(f"{INTERACTIONS_URL}/1/favorite")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_toggle_favorite_success(client_with_mocks, mock_interaction_service, mock_auth):
    mock_interaction_service.toggle_favorite.return_value = True
    response = client_with_mocks.post(f"{INTERACTIONS_URL}/1/favorite", headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() is True
    mock_interaction_service.toggle_favorite.assert_called_once_with(1, "test-uuid")

def test_get_my_favorites_unauthorized(client_with_mocks):
    response = client_with_mocks.get(f"{INTERACTIONS_URL}/me/favorites")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_my_favorites_success(client_with_mocks, mock_interaction_service, mock_auth):
    mock_interaction_service.get_user_favorites.return_value = [1, 2, 3]
    response = client_with_mocks.get(f"{INTERACTIONS_URL}/me/favorites", headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [1, 2, 3]
    mock_interaction_service.get_user_favorites.assert_called_once_with("test-uuid", 100, 0)

def test_set_rating_unauthorized(client_with_mocks):
    response = client_with_mocks.post(f"{INTERACTIONS_URL}/1/rating", json={"score": 4})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_set_rating_invalid_score(client_with_mocks, mock_auth):
    # test score < 1
    response = client_with_mocks.post(f"{INTERACTIONS_URL}/1/rating", json={"score": 0}, headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # test score > 5
    response = client_with_mocks.post(f"{INTERACTIONS_URL}/1/rating", json={"score": 6}, headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_set_rating_success(client_with_mocks, mock_interaction_service, mock_auth):
    mock_interaction_service.set_rating.return_value = {"recipe_id": 1, "user_id": "test-uuid", "score": 4}
    response = client_with_mocks.post(f"{INTERACTIONS_URL}/1/rating", json={"score": 4}, headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_200_OK
    mock_interaction_service.set_rating.assert_called_once_with(1, "test-uuid", 4)

def test_delete_rating_unauthorized(client_with_mocks):
    response = client_with_mocks.delete(f"{INTERACTIONS_URL}/1/rating")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_delete_rating_success(client_with_mocks, mock_interaction_service, mock_auth):
    mock_interaction_service.delete_rating.return_value = True
    response = client_with_mocks.delete(f"{INTERACTIONS_URL}/1/rating", headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_200_OK
    mock_interaction_service.delete_rating.assert_called_once_with(1, "test-uuid")

def test_get_comments_unauthorized_but_successful(client_with_mocks, mock_interaction_service):
    # comments are public
    now = datetime.now(timezone.utc).isoformat()
    mock_interaction_service.get_comments.return_value = [
        {"id": 1, "recipe_id": 1, "user_id": "other", "content": "hello", "created_at": now, "updated_at": now}
    ]
    mock_interaction_service.get_comment_reactions.return_value = {
        1: {"counts": {"LIKE": 1}, "user_reaction": None}
    }
    
    response = client_with_mocks.get(f"{INTERACTIONS_URL}/1/comments")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "hello"
    assert data[0]["reactions"]["counts"]["LIKE"] == 1
    
    mock_interaction_service.get_comments.assert_called_once_with(1, 100, 0)
    mock_interaction_service.get_comment_reactions.assert_called_once_with([1], None)

def test_get_comments_with_auth(client_with_mocks, mock_interaction_service, mock_auth):
    now = datetime.now(timezone.utc).isoformat()
    mock_interaction_service.get_comments.return_value = [
        {"id": 1, "recipe_id": 1, "user_id": "other", "content": "hello", "created_at": now, "updated_at": now}
    ]
    mock_interaction_service.get_comment_reactions.return_value = {
        1: {"counts": {"LIKE": 1}, "user_reaction": "LIKE"}
    }
    
    response = client_with_mocks.get(f"{INTERACTIONS_URL}/1/comments", headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_200_OK
    
    mock_interaction_service.get_comments.assert_called_once_with(1, 100, 0)
    mock_interaction_service.get_comment_reactions.assert_called_once_with([1], "test-uuid")

def test_add_comment_unauthorized(client_with_mocks):
    response = client_with_mocks.post(f"{INTERACTIONS_URL}/1/comments", json={"content": "hello"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_add_comment_empty(client_with_mocks, mock_auth):
    response = client_with_mocks.post(f"{INTERACTIONS_URL}/1/comments", json={"content": "   "}, headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_add_comment_success(client_with_mocks, mock_interaction_service, mock_auth):
    now = datetime.now(timezone.utc).isoformat()
    mock_interaction_service.add_comment.return_value = {
        "id": 1, "recipe_id": 1, "user_id": "test-uuid", "content": "hello", "created_at": now, "updated_at": now
    }
    response = client_with_mocks.post(f"{INTERACTIONS_URL}/1/comments", json={"content": "hello"}, headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["content"] == "hello"
    assert data["reactions"] == {"counts": {}, "user_reaction": None}
    
    mock_interaction_service.add_comment.assert_called_once_with(1, "test-uuid", "hello")

def test_update_comment_unauthorized(client_with_mocks):
    response = client_with_mocks.put(f"{INTERACTIONS_URL}/comments/1", json={"content": "hello"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_update_comment_empty(client_with_mocks, mock_auth):
    response = client_with_mocks.put(f"{INTERACTIONS_URL}/comments/1", json={"content": "   "}, headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_update_comment_not_found(client_with_mocks, mock_interaction_service, mock_auth):
    mock_interaction_service.update_comment.return_value = None
    response = client_with_mocks.put(f"{INTERACTIONS_URL}/comments/1", json={"content": "hello"}, headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_comment_success(client_with_mocks, mock_interaction_service, mock_auth):
    now = datetime.now(timezone.utc).isoformat()
    mock_interaction_service.update_comment.return_value = {
        "id": 1, "recipe_id": 1, "user_id": "test-uuid", "content": "hello updated", "created_at": now, "updated_at": now
    }
    mock_interaction_service.get_comment_reactions.return_value = {
        1: {"counts": {"LIKE": 1}, "user_reaction": "LIKE"}
    }
    
    response = client_with_mocks.put(f"{INTERACTIONS_URL}/comments/1", json={"content": "hello updated"}, headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["content"] == "hello updated"
    assert data["reactions"] == {"counts": {"LIKE": 1}, "user_reaction": "LIKE"}
    
    mock_interaction_service.update_comment.assert_called_once_with(1, "test-uuid", "hello updated")
    mock_interaction_service.get_comment_reactions.assert_called_once_with([1], "test-uuid")

def test_delete_comment_unauthorized(client_with_mocks):
    response = client_with_mocks.delete(f"{INTERACTIONS_URL}/comments/1")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_delete_comment_not_found(client_with_mocks, mock_interaction_service, mock_auth):
    mock_interaction_service.delete_comment.return_value = False
    response = client_with_mocks.delete(f"{INTERACTIONS_URL}/comments/1", headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_comment_success(client_with_mocks, mock_interaction_service, mock_auth):
    mock_interaction_service.delete_comment.return_value = True
    response = client_with_mocks.delete(f"{INTERACTIONS_URL}/comments/1", headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_interaction_service.delete_comment.assert_called_once_with(1, "test-uuid", False)

def test_delete_comment_superuser(client_with_mocks, mock_interaction_service, mock_auth_superuser):
    mock_interaction_service.delete_comment.return_value = True
    response = client_with_mocks.delete(f"{INTERACTIONS_URL}/comments/1", headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_interaction_service.delete_comment.assert_called_once_with(1, "admin-uuid", True)

def test_toggle_reaction_unauthorized(client_with_mocks):
    response = client_with_mocks.post(f"{INTERACTIONS_URL}/comments/1/reactions", json={"reaction_type": "LIKE"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_toggle_reaction_success(client_with_mocks, mock_interaction_service, mock_auth):
    mock_interaction_service.toggle_reaction.return_value = {"reaction": "LIKE"}
    response = client_with_mocks.post(f"{INTERACTIONS_URL}/comments/1/reactions", json={"reaction_type": "LIKE"}, headers={"Authorization": "Bearer fake"})
    assert response.status_code == status.HTTP_200_OK
    mock_interaction_service.toggle_reaction.assert_called_once_with(1, "test-uuid", "LIKE")
