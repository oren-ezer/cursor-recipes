"""Tests for the /api/v1/ai endpoints.

Uses FastAPI dependency overrides to mock the AI service and authentication,
so no real LLM calls or database connections are needed.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import status
from fastapi.testclient import TestClient

from src.main import app
from src.core.config import settings
from src.api.v1.endpoints.ai import get_ai_service, calculate_cost
from src.services.ai_service import AIService
from openai import AuthenticationError, RateLimitError, APIError


AI_PREFIX = f"{settings.API_V1_STR}/ai"

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_ai_service():
    """Create a mock AIService with async methods."""
    svc = Mock(spec=AIService)
    svc.call_llm = AsyncMock()
    svc.suggest_tags = AsyncMock()
    svc.parse_natural_language_search = AsyncMock()
    svc.calculate_nutrition = AsyncMock()
    return svc


def _auth_headers(is_superuser=False):
    """Return an auth header dict. The middleware is patched so the token value doesn't matter."""
    return {"Authorization": "Bearer fake-token"}


def _fake_user(is_superuser=False):
    return {
        "id": 1,
        "uuid": "test-user-uuid",
        "email": "test@example.com",
        "is_superuser": is_superuser,
        "is_active": True,
    }


@pytest.fixture
def client_with_ai(mock_ai_service):
    """TestClient with overridden AI service dependency and authenticated user."""
    app.dependency_overrides[get_ai_service] = lambda: mock_ai_service
    with TestClient(app) as c:
        yield c, mock_ai_service
    app.dependency_overrides.pop(get_ai_service, None)


# ──────────────────────────────────────────────────────────────────────────────
# calculate_cost (pure function)
# ──────────────────────────────────────────────────────────────────────────────

class TestCalculateCost:
    def test_gpt4o_mini_cost(self):
        tokens = {"prompt": 1000, "completion": 500}
        cost = calculate_cost(tokens, "gpt-4o-mini")
        assert cost == pytest.approx(0.00045, abs=1e-6)

    def test_gpt4o_cost(self):
        tokens = {"prompt": 1000, "completion": 500}
        cost = calculate_cost(tokens, "gpt-4o")
        assert cost == pytest.approx(0.0075, abs=1e-6)

    def test_gpt35_turbo_cost(self):
        tokens = {"prompt": 1000, "completion": 500}
        cost = calculate_cost(tokens, "gpt-3.5-turbo")
        assert cost == pytest.approx(0.00125, abs=1e-6)

    def test_unknown_model_uses_gpt4o_mini_pricing(self):
        tokens = {"prompt": 1000, "completion": 500}
        cost_unknown = calculate_cost(tokens, "unknown-model")
        cost_mini = calculate_cost(tokens, "gpt-4o-mini")
        assert cost_unknown == cost_mini

    def test_zero_tokens(self):
        tokens = {"prompt": 0, "completion": 0}
        assert calculate_cost(tokens, "gpt-4o") == 0.0


# ──────────────────────────────────────────────────────────────────────────────
# POST /ai/test
# ──────────────────────────────────────────────────────────────────────────────

class TestAITestEndpoint:
    def test_unauthenticated_returns_401(self, client_with_ai):
        client, _ = client_with_ai
        resp = client.post(f"{AI_PREFIX}/test", json={"user_prompt": "hello"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_admin_returns_403(self, client_with_ai):
        client, _ = client_with_ai
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user(is_superuser=False)
            resp = client.post(
                f"{AI_PREFIX}/test",
                json={"user_prompt": "hello"},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_success(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.call_llm.return_value = {
            "content": "Test response",
            "tokens_used": {"prompt": 100, "completion": 50, "total": 150},
            "model": "gpt-4o-mini",
            "finish_reason": "stop",
        }
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user(is_superuser=True)
            resp = client.post(
                f"{AI_PREFIX}/test",
                json={"user_prompt": "Say hello"},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["content"] == "Test response"
        assert data["model"] == "gpt-4o-mini"
        assert "estimated_cost" in data

    def test_authentication_error_returns_500(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.call_llm.side_effect = AuthenticationError(
            message="bad key", response=Mock(status_code=401), body=None
        )
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user(is_superuser=True)
            resp = client.post(
                f"{AI_PREFIX}/test",
                json={"user_prompt": "test"},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "authentication" in resp.json()["detail"].lower()

    def test_rate_limit_error_returns_429(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.call_llm.side_effect = RateLimitError(
            message="rate limited", response=Mock(status_code=429), body=None
        )
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user(is_superuser=True)
            resp = client.post(
                f"{AI_PREFIX}/test",
                json={"user_prompt": "test"},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_api_error_returns_503(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.call_llm.side_effect = APIError(
            message="server error", request=Mock(), body=None
        )
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user(is_superuser=True)
            resp = client.post(
                f"{AI_PREFIX}/test",
                json={"user_prompt": "test"},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_generic_exception_returns_500(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.call_llm.side_effect = RuntimeError("unexpected")
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user(is_superuser=True)
            resp = client.post(
                f"{AI_PREFIX}/test",
                json={"user_prompt": "test"},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_validation_error_empty_prompt(self, client_with_ai):
        client, _ = client_with_ai
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user(is_superuser=True)
            resp = client.post(
                f"{AI_PREFIX}/test",
                json={"user_prompt": ""},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ──────────────────────────────────────────────────────────────────────────────
# POST /ai/suggest-tags
# ──────────────────────────────────────────────────────────────────────────────

class TestSuggestTagsEndpoint:
    def test_unauthenticated_returns_401(self, client_with_ai):
        client, _ = client_with_ai
        resp = client.post(
            f"{AI_PREFIX}/suggest-tags",
            json={"recipe_title": "Test", "ingredients": ["flour"]}
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_success(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.suggest_tags.return_value = ["italian", "pasta", "dinner"]
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/suggest-tags",
                json={"recipe_title": "Spaghetti", "ingredients": ["pasta", "tomato"]},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["suggested_tags"] == ["italian", "pasta", "dinner"]
        assert 0.0 <= data["confidence"] <= 1.0

    def test_confidence_calculated_correctly(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.suggest_tags.return_value = ["a", "b"]
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/suggest-tags",
                json={"recipe_title": "Test", "ingredients": ["flour"]},
                headers=_auth_headers()
            )
        assert resp.json()["confidence"] == pytest.approx(0.4)

    def test_confidence_capped_at_1(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.suggest_tags.return_value = ["a", "b", "c", "d", "e", "f", "g"]
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/suggest-tags",
                json={"recipe_title": "Test", "ingredients": ["flour"]},
                headers=_auth_headers()
            )
        assert resp.json()["confidence"] == 1.0

    def test_service_error_returns_503(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.suggest_tags.side_effect = RuntimeError("LLM down")
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/suggest-tags",
                json={"recipe_title": "Test", "ingredients": ["flour"]},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_validation_missing_ingredients(self, client_with_ai):
        client, _ = client_with_ai
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/suggest-tags",
                json={"recipe_title": "Test", "ingredients": []},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_passes_existing_tags(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.suggest_tags.return_value = ["new-tag"]
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/suggest-tags",
                json={
                    "recipe_title": "Test",
                    "ingredients": ["flour"],
                    "existing_tags": ["existing"]
                },
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_200_OK
        call_kwargs = mock_svc.suggest_tags.call_args[1]
        assert call_kwargs["existing_tags"] == ["existing"]


# ──────────────────────────────────────────────────────────────────────────────
# POST /ai/search
# ──────────────────────────────────────────────────────────────────────────────

class TestNaturalLanguageSearchEndpoint:
    def test_unauthenticated_returns_401(self, client_with_ai):
        client, _ = client_with_ai
        resp = client.post(
            f"{AI_PREFIX}/search",
            json={"query": "quick pasta"}
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_success(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.parse_natural_language_search.return_value = {
            "keywords": ["pasta"],
            "tags": ["italian"],
            "max_prep_time": None,
            "max_cook_time": 30,
            "difficulty": "Easy",
        }
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/search",
                json={"query": "easy Italian pasta under 30 min"},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["keywords"] == ["pasta"]
        assert data["max_cook_time"] == 30

    def test_service_error_returns_503(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.parse_natural_language_search.side_effect = RuntimeError("fail")
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/search",
                json={"query": "test"},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_validation_empty_query(self, client_with_ai):
        client, _ = client_with_ai
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/search",
                json={"query": ""},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_validation_query_too_long(self, client_with_ai):
        client, _ = client_with_ai
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/search",
                json={"query": "x" * 501},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ──────────────────────────────────────────────────────────────────────────────
# POST /ai/nutrition
# ──────────────────────────────────────────────────────────────────────────────

class TestNutritionEndpoint:
    def test_unauthenticated_returns_401(self, client_with_ai):
        client, _ = client_with_ai
        resp = client.post(
            f"{AI_PREFIX}/nutrition",
            json={"ingredients": [{"name": "flour", "amount": "1 cup"}]}
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_success(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.calculate_nutrition.return_value = {
            "calories": 350.0,
            "protein_g": 10.0,
            "carbs_g": 50.0,
            "fat_g": 12.0,
            "fiber_g": 3.0,
            "sodium_mg": 400.0,
        }
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/nutrition",
                json={
                    "ingredients": [
                        {"name": "chicken", "amount": "200g"},
                        {"name": "rice", "amount": "1 cup"}
                    ],
                    "servings": 2
                },
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["calories"] == 350.0
        assert data["protein_g"] == 10.0

    def test_passes_servings_to_service(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.calculate_nutrition.return_value = {
            "calories": 100.0, "protein_g": 5.0, "carbs_g": 20.0,
            "fat_g": 2.0, "fiber_g": 1.0, "sodium_mg": 100.0,
        }
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/nutrition",
                json={
                    "ingredients": [{"name": "flour", "amount": "500g"}],
                    "servings": 4
                },
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_200_OK
        call_kwargs = mock_svc.calculate_nutrition.call_args[1]
        assert call_kwargs["servings"] == 4

    def test_service_error_returns_503(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.calculate_nutrition.side_effect = RuntimeError("fail")
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/nutrition",
                json={"ingredients": [{"name": "flour", "amount": "1 cup"}]},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_validation_empty_ingredients(self, client_with_ai):
        client, _ = client_with_ai
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/nutrition",
                json={"ingredients": []},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_validation_invalid_servings(self, client_with_ai):
        client, _ = client_with_ai
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/nutrition",
                json={
                    "ingredients": [{"name": "flour", "amount": "1 cup"}],
                    "servings": 0
                },
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_default_servings_is_1(self, client_with_ai):
        client, mock_svc = client_with_ai
        mock_svc.calculate_nutrition.return_value = {
            "calories": 100.0, "protein_g": 5.0, "carbs_g": 20.0,
            "fat_g": 2.0, "fiber_g": 1.0, "sodium_mg": 100.0,
        }
        with patch("src.main._get_current_user_from_token", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = _fake_user()
            resp = client.post(
                f"{AI_PREFIX}/nutrition",
                json={"ingredients": [{"name": "egg", "amount": "1"}]},
                headers=_auth_headers()
            )
        assert resp.status_code == status.HTTP_200_OK
        call_kwargs = mock_svc.calculate_nutrition.call_args[1]
        assert call_kwargs["servings"] == 1
