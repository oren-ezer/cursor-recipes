"""Tests for the /api/v1/images endpoints.

Uses FastAPI dependency overrides to mock storage backend and authentication.
"""

import pytest
from io import BytesIO
from unittest.mock import Mock, patch, call

from fastapi.testclient import TestClient
from fastapi import status

from src.main import app
from src.core.config import settings
from src.services.image_storage import StoredImage, DatabaseStorage
from src.utils.dependencies import get_image_storage, get_database_session


IMAGES_PREFIX = f"{settings.API_V1_STR}/images"

TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
    b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)

OWNER_UUID = "owner-uuid"
OTHER_UUID = "other-uuid"


def _fake_user(uuid=OWNER_UUID, is_superuser=False):
    return {
        "id": 1,
        "uuid": uuid,
        "email": "test@example.com",
        "is_superuser": is_superuser,
        "is_active": True,
    }


def _owned_recipe(recipe_id=42, user_id=OWNER_UUID):
    recipe = Mock()
    recipe.id = recipe_id
    recipe.user_id = user_id
    recipe.image_url = None
    return recipe


def _image_row(
    uuid="img-uuid-1",
    recipe_id=42,
    is_primary=False,
    filename="photo.png",
    size_bytes=len(TINY_PNG),
):
    row = Mock()
    row.uuid = uuid
    row.recipe_id = recipe_id
    row.is_primary = is_primary
    row.filename = filename
    row.size_bytes = size_bytes
    row.created_at = None
    return row


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
    storage.get_serving_url.side_effect = lambda image_id: f"/api/v1/images/{image_id}"
    storage.retrieve.return_value = (TINY_PNG, "image/png")
    return storage


@pytest.fixture
def mock_db():
    """Mock DB session with recipe ownership + image row helpers."""
    session = Mock()
    recipe = _owned_recipe()
    image = _image_row(is_primary=False)

    def exec_side_effect(statement):
        result = Mock()
        # Default: first() returns image; tests override as needed
        result.first = Mock(return_value=image)
        result.all = Mock(return_value=[image])
        return result

    session.exec = Mock(side_effect=exec_side_effect)
    session.add = Mock()
    session.commit = Mock()
    session.flush = Mock()
    session.refresh = Mock()
    session._recipe = recipe
    session._image = image
    return session


@pytest.fixture
def client_with_storage(mock_storage, mock_db):
    app.dependency_overrides[get_image_storage] = lambda: mock_storage
    app.dependency_overrides[get_database_session] = lambda: mock_db
    with TestClient(app) as c:
        yield c, mock_storage, mock_db
    app.dependency_overrides.pop(get_image_storage, None)
    app.dependency_overrides.pop(get_database_session, None)


def _upload_files(*names):
    return [("images", (name, BytesIO(TINY_PNG), "image/png")) for name in names]


def _auth_headers():
    return {"Authorization": "Bearer fake-token"}


# ──────────────────────────────────────────────────────────────────────────────
# POST /images/upload
# ──────────────────────────────────────────────────────────────────────────────

class TestUploadImages:
    def test_upload_requires_auth(self, client_with_storage):
        client, _, _ = client_with_storage
        resp = client.post(
            f"{IMAGES_PREFIX}/upload",
            data={"recipe_id": "42"},
            files=_upload_files("photo.png"),
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_requires_recipe_id(self, client_with_storage):
        client, _, _ = client_with_storage
        with patch("src.main._get_current_user_from_token", return_value=_fake_user()):
            resp = client.post(
                f"{IMAGES_PREFIX}/upload",
                files=_upload_files("photo.png"),
                headers=_auth_headers(),
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("src.main._get_current_user_from_token", return_value=_fake_user(uuid=OTHER_UUID))
    def test_upload_forbidden_for_non_owner(self, _mock_auth, client_with_storage):
        client, _, mock_db = client_with_storage

        def exec_side_effect(_statement):
            result = Mock()
            result.first = Mock(return_value=_owned_recipe())
            result.all = Mock(return_value=[])
            return result

        mock_db.exec = Mock(side_effect=exec_side_effect)

        resp = client.post(
            f"{IMAGES_PREFIX}/upload",
            data={"recipe_id": "42"},
            files=_upload_files("photo.png"),
            headers=_auth_headers(),
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_upload_single_image(self, _mock_auth, client_with_storage):
        client, mock_storage, mock_db = client_with_storage
        recipe = _owned_recipe()
        image = _image_row(is_primary=False)

        call_count = {"n": 0}

        def exec_side_effect(_statement):
            call_count["n"] += 1
            result = Mock()
            # 1) ownership recipe lookup
            # 2) has_primary check -> None
            # 3) reload stored image row
            if call_count["n"] == 1:
                result.first = Mock(return_value=recipe)
            elif call_count["n"] == 2:
                result.first = Mock(return_value=None)
            else:
                result.first = Mock(return_value=image)
            result.all = Mock(return_value=[])
            return result

        mock_db.exec = Mock(side_effect=exec_side_effect)

        resp = client.post(
            f"{IMAGES_PREFIX}/upload",
            data={"recipe_id": "42"},
            files=_upload_files("photo.png"),
            headers=_auth_headers(),
        )
        assert resp.status_code == status.HTTP_201_CREATED
        body = resp.json()
        assert len(body["images"]) == 1
        assert body["images"][0]["image_id"] == "img-uuid-1"
        assert body["images"][0]["is_primary"] is True
        assert body["images"][0]["serving_url"].endswith("/images/img-uuid-1")
        mock_storage.store.assert_called_once()
        assert mock_storage.store.call_args[0][3] == 42  # recipe_id

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_upload_multiple_images(self, _mock_auth, client_with_storage):
        client, mock_storage, mock_db = client_with_storage
        recipe = _owned_recipe()
        images = [_image_row(uuid="img-uuid-1"), _image_row(uuid="img-uuid-2")]
        mock_storage.store.side_effect = [
            StoredImage("img-uuid-1", "img-uuid-1", "database"),
            StoredImage("img-uuid-2", "img-uuid-2", "database"),
        ]

        calls = {"n": 0}

        def exec_side_effect(_statement):
            calls["n"] += 1
            result = Mock()
            if calls["n"] == 1:
                result.first = Mock(return_value=recipe)
            elif calls["n"] == 2:
                result.first = Mock(return_value=None)  # no existing primary
            elif calls["n"] == 3:
                result.first = Mock(return_value=images[0])
            else:
                result.first = Mock(return_value=images[1])
            result.all = Mock(return_value=[])
            return result

        mock_db.exec = Mock(side_effect=exec_side_effect)

        resp = client.post(
            f"{IMAGES_PREFIX}/upload",
            data={"recipe_id": "42"},
            files=_upload_files("a.png", "b.png"),
            headers=_auth_headers(),
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert len(resp.json()["images"]) == 2
        assert mock_storage.store.call_count == 2

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_upload_rejects_unsupported_content_type(self, _mock_auth, client_with_storage):
        client, _, mock_db = client_with_storage
        mock_db.exec = Mock(return_value=Mock(first=Mock(return_value=_owned_recipe()), all=Mock(return_value=[])))
        resp = client.post(
            f"{IMAGES_PREFIX}/upload",
            data={"recipe_id": "42"},
            files=[("images", ("doc.pdf", BytesIO(b"%PDF-1.4"), "application/pdf"))],
            headers=_auth_headers(),
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "unsupported type" in resp.json()["detail"]

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_upload_rejects_oversized_file(self, _mock_auth, client_with_storage):
        client, _, mock_db = client_with_storage
        mock_db.exec = Mock(return_value=Mock(first=Mock(return_value=_owned_recipe()), all=Mock(return_value=[])))
        with patch.object(settings, "MAX_IMAGE_UPLOAD_SIZE_MB", 0):
            resp = client.post(
                f"{IMAGES_PREFIX}/upload",
                data={"recipe_id": "42"},
                files=_upload_files("big.png"),
                headers=_auth_headers(),
            )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceeds" in resp.json()["detail"]

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_upload_rejects_too_many_files(self, _mock_auth, client_with_storage):
        client, _, mock_db = client_with_storage
        mock_db.exec = Mock(return_value=Mock(first=Mock(return_value=_owned_recipe()), all=Mock(return_value=[])))
        with patch.object(settings, "MAX_IMAGES_PER_UPLOAD", 1):
            resp = client.post(
                f"{IMAGES_PREFIX}/upload",
                data={"recipe_id": "42"},
                files=_upload_files("a.png", "b.png"),
                headers=_auth_headers(),
            )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Maximum" in resp.json()["detail"]


# ──────────────────────────────────────────────────────────────────────────────
# GET /images/recipe/{recipe_id}
# ──────────────────────────────────────────────────────────────────────────────

class TestGetRecipeImages:
    def test_list_recipe_images_includes_is_primary(self, client_with_storage):
        client, _, mock_db = client_with_storage
        primary = _image_row(uuid="p1", is_primary=True, filename="primary.png")
        secondary = _image_row(uuid="s1", is_primary=False, filename="other.png")
        mock_db.exec = Mock(return_value=Mock(all=Mock(return_value=[primary, secondary]), first=Mock(return_value=None)))

        resp = client.get(f"{IMAGES_PREFIX}/recipe/42")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert len(body["images"]) == 2
        assert body["images"][0]["is_primary"] is True
        assert body["images"][0]["image_id"] == "p1"
        assert body["images"][1]["is_primary"] is False


# ──────────────────────────────────────────────────────────────────────────────
# PATCH /images/{uuid}/primary
# ──────────────────────────────────────────────────────────────────────────────

class TestSetPrimaryImage:
    def test_set_primary_requires_auth(self, client_with_storage):
        client, _, _ = client_with_storage
        resp = client.patch(f"{IMAGES_PREFIX}/img-uuid-1/primary")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_set_primary_success(self, _mock_auth, client_with_storage):
        client, mock_storage, mock_db = client_with_storage
        recipe = _owned_recipe()
        image = _image_row(uuid="img-uuid-2", is_primary=False)
        old_primary = _image_row(uuid="img-uuid-1", is_primary=True)

        calls = {"n": 0}

        def exec_side_effect(_statement):
            calls["n"] += 1
            result = Mock()
            if calls["n"] == 1:
                result.first = Mock(return_value=image)  # load image
            elif calls["n"] == 2:
                result.first = Mock(return_value=recipe)  # ownership
            else:
                result.all = Mock(return_value=[old_primary])  # clear primaries
                result.first = Mock(return_value=None)
            return result

        mock_db.exec = Mock(side_effect=exec_side_effect)

        resp = client.patch(
            f"{IMAGES_PREFIX}/img-uuid-2/primary",
            headers=_auth_headers(),
        )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["image_id"] == "img-uuid-2"
        assert body["is_primary"] is True
        assert image.is_primary is True
        assert old_primary.is_primary is False
        assert recipe.image_url == "/api/v1/images/img-uuid-2"

    @patch("src.main._get_current_user_from_token", return_value=_fake_user(uuid=OTHER_UUID))
    def test_set_primary_forbidden(self, _mock_auth, client_with_storage):
        client, _, mock_db = client_with_storage
        image = _image_row()
        recipe = _owned_recipe()

        calls = {"n": 0}

        def exec_side_effect(_statement):
            calls["n"] += 1
            result = Mock()
            result.first = Mock(return_value=image if calls["n"] == 1 else recipe)
            result.all = Mock(return_value=[])
            return result

        mock_db.exec = Mock(side_effect=exec_side_effect)

        resp = client.patch(
            f"{IMAGES_PREFIX}/img-uuid-1/primary",
            headers=_auth_headers(),
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ──────────────────────────────────────────────────────────────────────────────
# GET /images/{image_uuid}
# ──────────────────────────────────────────────────────────────────────────────

class TestGetImage:
    def test_get_image_returns_bytes(self, client_with_storage):
        client, mock_storage, _ = client_with_storage
        resp = client.get(f"{IMAGES_PREFIX}/some-uuid")
        assert resp.status_code == 200
        assert resp.content == TINY_PNG
        assert resp.headers["content-type"] == "image/png"
        assert "max-age" in resp.headers.get("cache-control", "")

    def test_get_image_not_found(self, client_with_storage):
        client, mock_storage, _ = client_with_storage
        mock_storage.retrieve.side_effect = ValueError("Image not found: bad-uuid")
        resp = client.get(f"{IMAGES_PREFIX}/bad-uuid")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in resp.json()["detail"].lower()

    def test_get_image_no_auth_required(self, client_with_storage):
        client, _, _ = client_with_storage
        resp = client.get(f"{IMAGES_PREFIX}/some-uuid")
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
# DELETE /images/{image_uuid}
# ──────────────────────────────────────────────────────────────────────────────

class TestDeleteImage:
    def test_delete_requires_auth(self, client_with_storage):
        client, _, _ = client_with_storage
        resp = client.delete(f"{IMAGES_PREFIX}/some-uuid")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_delete_image_success(self, _mock_auth, client_with_storage):
        client, mock_storage, mock_db = client_with_storage
        image = _image_row(is_primary=False)
        recipe = _owned_recipe()

        calls = {"n": 0}

        def exec_side_effect(_statement):
            calls["n"] += 1
            result = Mock()
            result.first = Mock(return_value=image if calls["n"] == 1 else recipe)
            result.all = Mock(return_value=[])
            return result

        mock_db.exec = Mock(side_effect=exec_side_effect)

        resp = client.delete(
            f"{IMAGES_PREFIX}/some-uuid",
            headers=_auth_headers(),
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        mock_storage.delete.assert_called_once_with("some-uuid")

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_delete_primary_promotes_next(self, _mock_auth, client_with_storage):
        client, mock_storage, mock_db = client_with_storage
        primary = _image_row(uuid="primary-uuid", is_primary=True)
        next_image = _image_row(uuid="next-uuid", is_primary=False)
        recipe = _owned_recipe()

        calls = {"n": 0}

        def exec_side_effect(_statement):
            calls["n"] += 1
            result = Mock()
            if calls["n"] == 1:
                result.first = Mock(return_value=primary)  # load image
            elif calls["n"] == 2:
                result.first = Mock(return_value=recipe)  # ownership
            elif calls["n"] == 3:
                result.first = Mock(return_value=next_image)  # next after delete
            else:
                result.first = Mock(return_value=recipe)  # recipe reload
            result.all = Mock(return_value=[])
            return result

        mock_db.exec = Mock(side_effect=exec_side_effect)

        resp = client.delete(
            f"{IMAGES_PREFIX}/primary-uuid",
            headers=_auth_headers(),
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert next_image.is_primary is True
        assert recipe.image_url == "/api/v1/images/next-uuid"

    @patch("src.main._get_current_user_from_token", return_value=_fake_user())
    def test_delete_image_not_found(self, _mock_auth, client_with_storage, mock_db):
        client, _, _ = client_with_storage
        mock_db.exec = Mock(return_value=Mock(first=Mock(return_value=None), all=Mock(return_value=[])))
        resp = client.delete(
            f"{IMAGES_PREFIX}/bad-uuid",
            headers=_auth_headers(),
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in resp.json()["detail"].lower()


# ──────────────────────────────────────────────────────────────────────────────
# Associate endpoint removed
# ──────────────────────────────────────────────────────────────────────────────

class TestAssociateRemoved:
    def test_associate_endpoint_gone(self, client_with_storage):
        client, _, _ = client_with_storage
        with patch("src.main._get_current_user_from_token", return_value=_fake_user()):
            resp = client.patch(
                f"{IMAGES_PREFIX}/associate",
                json={"image_ids": ["x"], "recipe_id": 1},
                headers=_auth_headers(),
            )
        assert resp.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED)
