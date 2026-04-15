"""Tests for the /api/v1/images endpoints.

Uses FastAPI dependency overrides to mock storage backend and authentication.
"""

import pytest
from io import BytesIO
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from fastapi import status

from src.main import app
from src.core.config import settings
from src.services.image_storage import StoredImage, ImageStorageBackend, DatabaseStorage
from src.utils.dependencies import get_image_storage, get_database_session


IMAGES_PREFIX = f"{settings.API_V1_STR}/images"

TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
    b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _fake_user(is_superuser=False):
    return {
        "id": 1,
        "uuid": "test-user-uuid",
        "email": "test@example.com",
        "is_superuser": is_superuser,
        "is_active": True,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_storage():
    storage = Mock(spec=DatabaseStorage)
    storage.store.return_value = StoredImage(
        image_id="img-uuid-1",
        storage_ref="img-uuid-1",
        storage_backend="database",
    )
    storage.get_serving_url.return_value = "/api/v1/images/img-uuid-1"
    storage.retrieve.return_value = (TINY_PNG, "image/png")
    return storage


@pytest.fixture
def mock_db():
    """Mock DB session that returns a RecipeImage-like object when queried."""
    session = Mock()
    mock_image = Mock()
    mock_image.recipe_id = None
    mock_image.is_primary = False
    session.exec = Mock(return_value=Mock(first=Mock(return_value=mock_image)))
    session.add = Mock()
    session.commit = Mock()
    return session


@pytest.fixture
def client_with_storage(mock_storage, mock_db):
    app.dependency_overrides[get_image_storage] = lambda: mock_storage
    app.dependency_overrides[get_database_session] = lambda: mock_db
    with TestClient(app) as c:
        yield c, mock_storage
    app.dependency_overrides.pop(get_image_storage, None)
    app.dependency_overrides.pop(get_database_session, None)


# ──────────────────────────────────────────────────────────────────────────────
# POST /images/upload
# ──────────────────────────────────────────────────────────────────────────────

class TestUploadImages:
    def test_upload_requires_auth(self, client_with_storage):
        client, _ = client_with_storage
        resp = client.post(
            f"{IMAGES_PREFIX}/upload",
            files=[("images", ("photo.png", BytesIO(TINY_PNG), "image/png"))],
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_upload_single_image(self, _mock_auth, client_with_storage):
        client, mock_storage = client_with_storage
        resp = client.post(
            f"{IMAGES_PREFIX}/upload",
            files=[("images", ("photo.png", BytesIO(TINY_PNG), "image/png"))],
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        body = resp.json()
        assert len(body["images"]) == 1
        assert body["images"][0]["image_id"] == "img-uuid-1"
        assert body["images"][0]["serving_url"].endswith("/images/img-uuid-1")
        mock_storage.store.assert_called_once()

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_upload_multiple_images(self, _mock_auth, client_with_storage):
        client, mock_storage = client_with_storage
        files = [
            ("images", ("a.png", BytesIO(TINY_PNG), "image/png")),
            ("images", ("b.png", BytesIO(TINY_PNG), "image/png")),
        ]
        resp = client.post(
            f"{IMAGES_PREFIX}/upload",
            files=files,
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert len(resp.json()["images"]) == 2
        assert mock_storage.store.call_count == 2

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_upload_rejects_unsupported_content_type(self, _mock_auth, client_with_storage):
        client, _ = client_with_storage
        resp = client.post(
            f"{IMAGES_PREFIX}/upload",
            files=[("images", ("doc.pdf", BytesIO(b"%PDF-1.4"), "application/pdf"))],
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "unsupported type" in resp.json()["detail"]

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_upload_rejects_oversized_file(self, _mock_auth, client_with_storage):
        client, _ = client_with_storage
        with patch.object(settings, "MAX_IMAGE_UPLOAD_SIZE_MB", 0):
            resp = client.post(
                f"{IMAGES_PREFIX}/upload",
                files=[("images", ("big.png", BytesIO(TINY_PNG), "image/png"))],
                headers={"Authorization": "Bearer fake-token"},
            )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceeds" in resp.json()["detail"]

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_upload_rejects_too_many_files(self, _mock_auth, client_with_storage):
        client, _ = client_with_storage
        with patch.object(settings, "MAX_IMAGES_PER_UPLOAD", 1):
            files = [
                ("images", ("a.png", BytesIO(TINY_PNG), "image/png")),
                ("images", ("b.png", BytesIO(TINY_PNG), "image/png")),
            ]
            resp = client.post(
                f"{IMAGES_PREFIX}/upload",
                files=files,
                headers={"Authorization": "Bearer fake-token"},
            )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Maximum" in resp.json()["detail"]


# ──────────────────────────────────────────────────────────────────────────────
# GET /images/{image_uuid}
# ──────────────────────────────────────────────────────────────────────────────

class TestGetImage:
    def test_get_image_returns_bytes(self, client_with_storage):
        client, mock_storage = client_with_storage
        resp = client.get(f"{IMAGES_PREFIX}/some-uuid")
        assert resp.status_code == 200
        assert resp.content == TINY_PNG
        assert resp.headers["content-type"] == "image/png"
        assert "max-age" in resp.headers.get("cache-control", "")

    def test_get_image_not_found(self, client_with_storage):
        client, mock_storage = client_with_storage
        mock_storage.retrieve.side_effect = ValueError("Image not found: bad-uuid")
        resp = client.get(f"{IMAGES_PREFIX}/bad-uuid")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in resp.json()["detail"].lower()

    def test_get_image_no_auth_required(self, client_with_storage):
        """Image serving should work without authentication."""
        client, _ = client_with_storage
        resp = client.get(f"{IMAGES_PREFIX}/some-uuid")
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
# DELETE /images/{image_uuid}
# ──────────────────────────────────────────────────────────────────────────────

class TestDeleteImage:
    def test_delete_requires_auth(self, client_with_storage):
        client, _ = client_with_storage
        resp = client.delete(f"{IMAGES_PREFIX}/some-uuid")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_delete_image_success(self, _mock_auth, client_with_storage):
        client, mock_storage = client_with_storage
        resp = client.delete(
            f"{IMAGES_PREFIX}/some-uuid",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        mock_storage.delete.assert_called_once_with("some-uuid")

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_delete_image_not_found(self, _mock_auth, client_with_storage, mock_db):
        client, _ = client_with_storage
        mock_db.exec.return_value = Mock(first=Mock(return_value=None))
        resp = client.delete(
            f"{IMAGES_PREFIX}/bad-uuid",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in resp.json()["detail"].lower()
