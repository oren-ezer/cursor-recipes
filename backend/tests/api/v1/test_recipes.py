import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status, HTTPException
from datetime import datetime, timezone
import json

from src.main import app
from src.utils.dependencies import get_recipe_service_with_tags, get_interaction_service
from src.services.interaction_service import InteractionMetadata
from src.models.recipe import Recipe

@pytest.fixture
def mock_recipe_service():
    return MagicMock()

@pytest.fixture
def mock_interaction_service():
    return MagicMock()

@pytest.fixture
def mock_get_current_user():
    with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock:
        yield mock

@pytest.fixture
def client(mock_recipe_service, mock_interaction_service):
    app.dependency_overrides[get_recipe_service_with_tags] = lambda: mock_recipe_service
    app.dependency_overrides[get_interaction_service] = lambda: mock_interaction_service
    
    with TestClient(app) as c:
        yield c
        
    app.dependency_overrides.clear()

def test_read_recipes_public(client, mock_recipe_service, mock_interaction_service):
    mock_recipe_service.get_all_public_recipes_with_tags.return_value = {
        "recipes": [
            {
                "id": 1,
                "uuid": "test-uuid-1",
                "title": "Public Recipe",
                "description": "Desc",
                "ingredients": [{"name": "A", "amount": "1"}],
                "instructions": ["Step 1"],
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
        "limit": 100,
        "offset": 0
    }
    mock_meta = InteractionMetadata()
    mock_interaction_service.get_recipes_metadata.return_value = {1: mock_meta}

    response = client.get("/api/v1/recipes/")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["recipes"][0]["title"] == "Public Recipe"
    assert "interaction_meta" in response.json()["recipes"][0]
    mock_recipe_service.get_all_public_recipes_with_tags.assert_called_once()
    
def test_read_recipes_admin(client, mock_recipe_service, mock_interaction_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "admin-uuid", "is_superuser": True}
    
    mock_recipe_service.get_all_recipes_with_tags.return_value = {
        "recipes": [],
        "total": 0,
        "limit": 100,
        "offset": 0
    }
    mock_interaction_service.get_recipes_metadata.return_value = {}

    response = client.get("/api/v1/recipes/", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 200
    mock_recipe_service.get_all_recipes_with_tags.assert_called_once()
    mock_recipe_service.get_all_public_recipes_with_tags.assert_not_called()
    
def test_read_recipes_exception(client, mock_recipe_service):
    mock_recipe_service.get_all_public_recipes_with_tags.side_effect = Exception("DB Error")
    
    response = client.get("/api/v1/recipes/")
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to retrieve recipes"

def test_read_recipes_http_exception(client, mock_recipe_service):
    mock_recipe_service.get_all_public_recipes_with_tags.side_effect = HTTPException(status_code=400, detail="Bad")
    
    response = client.get("/api/v1/recipes/")
    assert response.status_code == 400

# My recipes (to cover lines 219-242)
def test_read_my_recipes_unauthorized(client):
    response = client.get("/api/v1/recipes/my")
    assert response.status_code == 401

def test_read_my_recipes_success(client, mock_recipe_service, mock_interaction_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid"}
    mock_recipe_service.get_all_my_recipes_with_tags.return_value = {
        "recipes": [],
        "total": 0,
        "limit": 10,
        "offset": 0
    }
    mock_interaction_service.get_recipes_metadata.return_value = {}

    response = client.get("/api/v1/recipes/my", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 200

def test_read_my_recipes_http_exception(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid"}
    mock_recipe_service.get_all_my_recipes_with_tags.side_effect = HTTPException(status_code=400, detail="Bad")
    
    response = client.get("/api/v1/recipes/my", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 400

def test_read_my_recipes_exception(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid"}
    mock_recipe_service.get_all_my_recipes_with_tags.side_effect = Exception("Error")
    
    response = client.get("/api/v1/recipes/my", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 500

def test_read_recipe_public_success(client, mock_recipe_service, mock_interaction_service):
    mock_recipe_service.get_recipe_with_tags.return_value = {
        "id": 1,
        "uuid": "test-uuid-1",
        "title": "Public Recipe",
        "description": "Desc",
        "ingredients": [{"name": "A", "amount": "1"}],
        "instructions": ["Step 1"],
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
    mock_interaction_service.get_recipes_metadata.return_value = {}

    response = client.get("/api/v1/recipes/1")
    assert response.status_code == 200
    assert response.json()["title"] == "Public Recipe"
    mock_recipe_service.get_recipe_with_tags.assert_called_once_with(1)

def test_read_recipe_not_found(client, mock_recipe_service):
    mock_recipe_service.get_recipe_with_tags.return_value = None

    response = client.get("/api/v1/recipes/1")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe with ID 1 not found"
    
def test_read_recipe_private_unauthorized(client, mock_recipe_service):
    mock_recipe_service.get_recipe_with_tags.return_value = {
        "id": 1,
        "is_public": False,
        "user_id": "owner-uuid",
        # other fields don't matter as we raise early
    }
    
    response = client.get("/api/v1/recipes/1")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required to view this private recipe"

def test_read_recipe_private_forbidden(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "other-uuid", "is_superuser": False}
    mock_recipe_service.get_recipe_with_tags.return_value = {
        "id": 1,
        "is_public": False,
        "user_id": "owner-uuid",
    }
    
    response = client.get("/api/v1/recipes/1", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to view this private recipe"

def test_read_recipe_private_owner(client, mock_recipe_service, mock_interaction_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "owner-uuid", "is_superuser": False}
    mock_recipe_service.get_recipe_with_tags.return_value = {
        "id": 1,
        "uuid": "test-uuid-1",
        "title": "Private Recipe",
        "description": "Desc",
        "ingredients": [{"name": "A", "amount": "1"}],
        "instructions": ["Step 1"],
        "preparation_time": 10,
        "cooking_time": 20,
        "servings": 2,
        "difficulty_level": "Easy",
        "user_id": "owner-uuid",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_public": False,
        "tags": []
    }
    mock_interaction_service.get_recipes_metadata.return_value = {}
    
    response = client.get("/api/v1/recipes/1", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 200

def test_read_recipe_exception(client, mock_recipe_service):
    mock_recipe_service.get_recipe_with_tags.side_effect = Exception("DB Error")
    
    response = client.get("/api/v1/recipes/1")
    assert response.status_code == 500

# Create Recipe
def test_create_recipe_unauthorized(client):
    recipe_in = {
        "title": "New Recipe",
        "ingredients": [{"name": "A", "amount": "1"}],
        "instructions": ["Step 1"],
        "preparation_time": 10,
        "cooking_time": 20,
        "servings": 2,
        "tag_ids": [1, 2, 3]
    }
    response = client.post("/api/v1/recipes/", json=recipe_in)
    assert response.status_code == 401

def test_create_recipe_success(client, mock_recipe_service, mock_interaction_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid"}
    
    recipe_in = {
        "title": "New Recipe",
        "description": "Some description",
        "image_url": "https://example.com/image.jpg",
        "ingredients": [{"name": "A", "amount": "1"}],
        "instructions": ["Step 1"],
        "preparation_time": 10,
        "cooking_time": 20,
        "servings": 2,
        "tag_ids": [1, 2, 3]
    }
    
    mock_recipe_service.create_recipe_with_tags.return_value = {
        "id": 1,
        "uuid": "test-uuid-1",
        "title": "New Recipe",
        "description": "",
        "ingredients": [{"name": "A", "amount": "1"}],
        "instructions": ["Step 1"],
        "preparation_time": 10,
        "cooking_time": 20,
        "servings": 2,
        "difficulty_level": "Easy",
        "user_id": "user-uuid",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_public": True,
        "tags": []
    }
    mock_interaction_service.get_recipes_metadata.return_value = {}

    response = client.post("/api/v1/recipes/", json=recipe_in, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 201
    mock_recipe_service.create_recipe_with_tags.assert_called_once()
    
def test_create_recipe_invalid_image_url(client, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid"}
    recipe_in = {
        "title": "New Recipe",
        "image_url": "invalid-url",
        "ingredients": [{"name": "A", "amount": "1"}],
        "instructions": ["Step 1"],
        "preparation_time": 10,
        "cooking_time": 20,
        "servings": 2,
        "tag_ids": [1, 2, 3]
    }
    response = client.post("/api/v1/recipes/", json=recipe_in, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 422

def test_create_recipe_valid_image_url_api(client, mock_recipe_service, mock_interaction_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid"}
    recipe_in = {
        "title": "New",
        "image_url": "/api/v1/images/1",
        "ingredients": [{"name": "A", "amount": "1"}],
        "instructions": ["Step 1"],
        "preparation_time": 1,
        "cooking_time": 1,
        "servings": 1,
        "tag_ids": [1, 2, 3]
    }
    mock_recipe_service.create_recipe_with_tags.return_value = {
        "id": 1, "uuid": "u", "title": "New", "description": "", 
        "ingredients": [{"name": "A", "amount": "1"}], "instructions": ["Step 1"], 
        "preparation_time": 1, "cooking_time": 1, "servings": 1, "difficulty_level": "Easy", 
        "user_id": "u", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc), 
        "is_public": True, "tags": []
    }
    mock_interaction_service.get_recipes_metadata.return_value = {}
    response = client.post("/api/v1/recipes/", json=recipe_in, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 201

def test_create_recipe_value_error(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid"}
    recipe_in = {
        "title": "New Recipe",
        "ingredients": [{"name": "A", "amount": "1"}],
        "instructions": ["Step 1"],
        "preparation_time": 10,
        "cooking_time": 20,
        "servings": 2,
        "tag_ids": [1, 2, 3]
    }
    mock_recipe_service.create_recipe_with_tags.side_effect = ValueError("Invalid data")
    
    response = client.post("/api/v1/recipes/", json=recipe_in, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 400

def test_create_recipe_exception(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid"}
    recipe_in = {
        "title": "New Recipe",
        "ingredients": [{"name": "A", "amount": "1"}],
        "instructions": ["Step 1"],
        "preparation_time": 10,
        "cooking_time": 20,
        "servings": 2,
        "tag_ids": [1, 2, 3]
    }
    mock_recipe_service.create_recipe_with_tags.side_effect = Exception("DB Error")
    
    response = client.post("/api/v1/recipes/", json=recipe_in, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 500

# Update Recipe
def test_update_recipe_unauthorized(client):
    response = client.put("/api/v1/recipes/1", json={"title": "Updated"})
    assert response.status_code == 401

def test_update_recipe_success(client, mock_recipe_service, mock_interaction_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    
    recipe_in = {
        "title": "Updated",
        "description": "New description",
        "instructions": ["New step"],
        "image_url": "https://example.com/image.jpg"
    }
    
    mock_recipe_service.update_recipe_with_tags.return_value = {
        "id": 1,
        "uuid": "test-uuid-1",
        "title": "Updated Recipe",
        "description": "",
        "ingredients": [],
        "instructions": [],
        "preparation_time": 10,
        "cooking_time": 20,
        "servings": 2,
        "difficulty_level": "Easy",
        "user_id": "user-uuid",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_public": True,
        "tags": []
    }
    mock_interaction_service.get_recipes_metadata.return_value = {}

    response = client.put("/api/v1/recipes/1", json=recipe_in, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 200
    mock_recipe_service.update_recipe_with_tags.assert_called_once()
    
def test_update_recipe_invalid_image_url(client, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    response = client.put("/api/v1/recipes/1", json={"image_url": "invalid-url"}, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 422
    
def test_update_recipe_valid_image_url(client, mock_recipe_service, mock_interaction_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    mock_recipe_service.update_recipe_with_tags.return_value = {
        "id": 1, "uuid": "u", "title": "U", "description": "", 
        "ingredients": [], "instructions": [], "preparation_time": 1, "cooking_time": 1, "servings": 1, "difficulty_level": "Easy", 
        "user_id": "u", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc), 
        "is_public": True, "tags": []
    }
    mock_interaction_service.get_recipes_metadata.return_value = {}
    response = client.put("/api/v1/recipes/1", json={"image_url": "/api/v1/images/1"}, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 200

def test_update_recipe_not_found(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    mock_recipe_service.update_recipe_with_tags.side_effect = ValueError("Recipe with ID 1 not found")
    
    response = client.put("/api/v1/recipes/1", json={"title": "Test"}, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 404

def test_update_recipe_forbidden(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    mock_recipe_service.update_recipe_with_tags.side_effect = ValueError("Not authorized to update this recipe")
    
    response = client.put("/api/v1/recipes/1", json={"title": "Test"}, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 403

def test_update_recipe_bad_request(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    mock_recipe_service.update_recipe_with_tags.side_effect = ValueError("Invalid data")
    
    response = client.put("/api/v1/recipes/1", json={"title": "Test"}, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 400
    
def test_update_recipe_exception(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    mock_recipe_service.update_recipe_with_tags.side_effect = Exception("DB error")
    
    response = client.put("/api/v1/recipes/1", json={"title": "Test"}, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 500

# Delete Recipe
def test_delete_recipe_unauthorized(client):
    response = client.delete("/api/v1/recipes/1")
    assert response.status_code == 401

def test_delete_recipe_success(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    mock_recipe_service.delete_recipe_with_tags.return_value = None
    
    response = client.delete("/api/v1/recipes/1", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 204
    mock_recipe_service.delete_recipe_with_tags.assert_called_once()

def test_delete_recipe_not_found(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    mock_recipe_service.delete_recipe_with_tags.side_effect = ValueError("Recipe with ID 1 not found")
    
    response = client.delete("/api/v1/recipes/1", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 404

def test_delete_recipe_forbidden(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    mock_recipe_service.delete_recipe_with_tags.side_effect = ValueError("Not authorized to delete this recipe")
    
    response = client.delete("/api/v1/recipes/1", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 403

def test_delete_recipe_bad_request(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    mock_recipe_service.delete_recipe_with_tags.side_effect = ValueError("Some other error")
    
    response = client.delete("/api/v1/recipes/1", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 400

def test_delete_recipe_exception(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    mock_recipe_service.delete_recipe_with_tags.side_effect = Exception("DB error")
    
    response = client.delete("/api/v1/recipes/1", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 500

# Export JSON
def test_export_json_unauthorized(client):
    response = client.get("/api/v1/recipes/1/export/json")
    assert response.status_code == 401

def test_export_json_forbidden(client, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    
    response = client.get("/api/v1/recipes/1/export/json", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 403

def test_export_json_success(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "admin-uuid", "is_superuser": True}
    mock_recipe_service.export_recipe_to_json.return_value = {"some": "data"}
    
    response = client.get("/api/v1/recipes/1/export/json", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 200
    assert response.json() == {"some": "data"}
    
def test_export_json_not_found(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "admin-uuid", "is_superuser": True}
    mock_recipe_service.export_recipe_to_json.side_effect = ValueError("Recipe with ID 1 not found")
    
    response = client.get("/api/v1/recipes/1/export/json", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 404

def test_export_json_bad_request(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "admin-uuid", "is_superuser": True}
    mock_recipe_service.export_recipe_to_json.side_effect = ValueError("Other error")
    
    response = client.get("/api/v1/recipes/1/export/json", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 400

def test_export_json_exception(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "admin-uuid", "is_superuser": True}
    mock_recipe_service.export_recipe_to_json.side_effect = Exception("DB error")
    
    response = client.get("/api/v1/recipes/1/export/json", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 500

# Export PDF
def test_export_pdf_unauthorized(client):
    response = client.get("/api/v1/recipes/1/export/pdf")
    assert response.status_code == 401

def test_export_pdf_not_found(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid"}
    mock_recipe_service.get_recipe.return_value = None
    
    response = client.get("/api/v1/recipes/1/export/pdf", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 404

def test_export_pdf_forbidden(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "other-uuid", "is_superuser": False}
    mock_recipe = MagicMock()
    mock_recipe.is_public = False
    mock_recipe.user_id = "owner-uuid"
    mock_recipe_service.get_recipe.return_value = mock_recipe
    
    response = client.get("/api/v1/recipes/1/export/pdf", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 403

def test_export_pdf_success(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid"}
    mock_recipe = MagicMock()
    mock_recipe.is_public = True
    mock_recipe.title = "Test"
    mock_recipe_service.get_recipe.return_value = mock_recipe
    mock_recipe_service.export_recipe_to_pdf.return_value = b"pdf_data"
    
    response = client.get("/api/v1/recipes/1/export/pdf", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 200
    assert response.content == b"pdf_data"
    assert response.headers["content-type"] == "application/pdf"

def test_export_pdf_value_error_not_found(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid"}
    mock_recipe = MagicMock()
    mock_recipe.is_public = True
    mock_recipe.title = "Test"
    mock_recipe_service.get_recipe.return_value = mock_recipe
    mock_recipe_service.export_recipe_to_pdf.side_effect = ValueError("Recipe with ID 1 not found")
    
    response = client.get("/api/v1/recipes/1/export/pdf", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 404
    
def test_export_pdf_value_error_other(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid"}
    mock_recipe = MagicMock()
    mock_recipe.is_public = True
    mock_recipe.title = "Test"
    mock_recipe_service.get_recipe.return_value = mock_recipe
    mock_recipe_service.export_recipe_to_pdf.side_effect = ValueError("Other error")
    
    response = client.get("/api/v1/recipes/1/export/pdf", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 400

def test_export_pdf_exception(client, mock_recipe_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid"}
    mock_recipe = MagicMock()
    mock_recipe.is_public = True
    mock_recipe.title = "Test"
    mock_recipe_service.get_recipe.return_value = mock_recipe
    mock_recipe_service.export_recipe_to_pdf.side_effect = Exception("DB error")
    
    response = client.get("/api/v1/recipes/1/export/pdf", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 500

def test_create_recipe_none_fields(client, mock_recipe_service, mock_interaction_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid"}
    
    recipe_in = {
        "title": "New Recipe",
        "description": None,
        "image_url": None,
        "ingredients": [{"name": "A", "amount": "1"}],
        "instructions": ["Step 1"],
        "preparation_time": 10,
        "cooking_time": 20,
        "servings": 2,
        "tag_ids": [1, 2, 3]
    }
    
    mock_recipe_service.create_recipe_with_tags.return_value = {
        "id": 2, "uuid": "test-uuid-2", "title": "New Recipe", "description": "",
        "ingredients": [{"name": "A", "amount": "1"}], "instructions": ["Step 1"],
        "preparation_time": 10, "cooking_time": 20, "servings": 2, "difficulty_level": "Easy",
        "user_id": "user-uuid", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
        "is_public": True, "tags": []
    }
    mock_interaction_service.get_recipes_metadata.return_value = {}

    response = client.post("/api/v1/recipes/", json=recipe_in, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 201

def test_update_recipe_none_fields(client, mock_recipe_service, mock_interaction_service, mock_get_current_user):
    mock_get_current_user.return_value = {"uuid": "user-uuid", "is_superuser": False}
    
    recipe_in = {
        "title": None,
        "description": None,
        "instructions": None,
        "image_url": None
    }
    
    mock_recipe_service.update_recipe_with_tags.return_value = {
        "id": 1, "uuid": "test-uuid-1", "title": "Updated", "description": "",
        "ingredients": [], "instructions": [], "preparation_time": 10, "cooking_time": 20,
        "servings": 2, "difficulty_level": "Easy", "user_id": "user-uuid",
        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
        "is_public": True, "tags": []
    }
    mock_interaction_service.get_recipes_metadata.return_value = {}

    response = client.put("/api/v1/recipes/1", json=recipe_in, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 200
