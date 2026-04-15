import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from src.services.image_storage import (
    DatabaseStorage,
    FileSystemStorage,
    S3Storage,
    StoredImage,
    create_storage_backend,
)
from src.models.recipe_image import RecipeImage


FAKE_BYTES = b"\x89PNG\r\n\x1a\nfake-image-data"
FAKE_UUID = "11111111-1111-1111-1111-111111111111"


# ──────────────────────────────────────────────────────────────────────────────
# DatabaseStorage
# ──────────────────────────────────────────────────────────────────────────────

class TestDatabaseStorage:
    @pytest.fixture
    def db(self):
        session = Mock()
        session.add = Mock()
        session.flush = Mock()
        return session

    @pytest.fixture
    def storage(self, db):
        return DatabaseStorage(db=db, api_prefix="/api/v1")

    @patch("src.services.image_storage.uuid.uuid4", return_value=FAKE_UUID)
    def test_store_inserts_row_and_returns_stored_image(self, _mock_uuid, storage, db):
        result = storage.store(FAKE_BYTES, "photo.jpg", "image/jpeg")

        assert isinstance(result, StoredImage)
        assert result.image_id == FAKE_UUID
        assert result.storage_backend == "database"
        db.add.assert_called_once()
        db.flush.assert_called_once()

        saved_image = db.add.call_args[0][0]
        assert isinstance(saved_image, RecipeImage)
        assert saved_image.data == FAKE_BYTES
        assert saved_image.filename == "photo.jpg"
        assert saved_image.content_type == "image/jpeg"
        assert saved_image.size_bytes == len(FAKE_BYTES)

    def test_retrieve_returns_bytes_and_content_type(self, storage, db):
        mock_image = Mock()
        mock_image.data = FAKE_BYTES
        mock_image.content_type = "image/png"
        db.exec = Mock(return_value=Mock(first=Mock(return_value=mock_image)))

        data, ct = storage.retrieve("some-uuid")
        assert data == FAKE_BYTES
        assert ct == "image/png"

    def test_retrieve_raises_when_not_found(self, storage, db):
        db.exec = Mock(return_value=Mock(first=Mock(return_value=None)))
        with pytest.raises(ValueError, match="Image not found"):
            storage.retrieve("missing-uuid")

    def test_delete_removes_row(self, storage, db):
        mock_image = Mock()
        db.exec = Mock(return_value=Mock(first=Mock(return_value=mock_image)))

        storage.delete("some-uuid")
        db.delete.assert_called_once_with(mock_image)
        db.flush.assert_called_once()

    def test_delete_no_op_when_not_found(self, storage, db):
        db.exec = Mock(return_value=Mock(first=Mock(return_value=None)))
        storage.delete("missing-uuid")
        db.delete.assert_not_called()

    def test_get_serving_url(self, storage):
        url = storage.get_serving_url("abc-123")
        assert url == "/api/v1/images/abc-123"

    def test_get_serving_url_strips_trailing_slash(self):
        db = Mock()
        s = DatabaseStorage(db=db, api_prefix="/api/v1/")
        assert s.get_serving_url("x") == "/api/v1/images/x"


# ──────────────────────────────────────────────────────────────────────────────
# FileSystemStorage
# ──────────────────────────────────────────────────────────────────────────────

class TestFileSystemStorage:
    @pytest.fixture
    def db(self):
        session = Mock()
        session.add = Mock()
        session.flush = Mock()
        return session

    @pytest.fixture
    def storage(self, db, tmp_path):
        return FileSystemStorage(db=db, base_path=tmp_path, api_prefix="/api/v1")

    @patch("src.services.image_storage.uuid.uuid4", return_value=FAKE_UUID)
    def test_store_writes_file_and_inserts_row(self, _mock_uuid, storage, db, tmp_path):
        result = storage.store(FAKE_BYTES, "photo.jpg", "image/jpeg")

        assert result.image_id == FAKE_UUID
        assert result.storage_backend == "filesystem"
        assert result.storage_ref == f"{FAKE_UUID}.jpg"

        written = (tmp_path / f"{FAKE_UUID}.jpg").read_bytes()
        assert written == FAKE_BYTES

        db.add.assert_called_once()
        saved = db.add.call_args[0][0]
        assert saved.data is None
        assert saved.storage_ref == f"{FAKE_UUID}.jpg"

    def test_retrieve_reads_file(self, storage, db, tmp_path):
        (tmp_path / "test.png").write_bytes(FAKE_BYTES)
        mock_image = Mock()
        mock_image.storage_ref = "test.png"
        mock_image.content_type = "image/png"
        db.exec = Mock(return_value=Mock(first=Mock(return_value=mock_image)))

        data, ct = storage.retrieve("some-uuid")
        assert data == FAKE_BYTES
        assert ct == "image/png"

    def test_retrieve_raises_when_not_found(self, storage, db):
        db.exec = Mock(return_value=Mock(first=Mock(return_value=None)))
        with pytest.raises(ValueError, match="Image not found"):
            storage.retrieve("missing-uuid")

    def test_retrieve_raises_when_file_missing(self, storage, db):
        mock_image = Mock()
        mock_image.storage_ref = "nonexistent.jpg"
        db.exec = Mock(return_value=Mock(first=Mock(return_value=mock_image)))
        with pytest.raises(ValueError, match="Image file missing from disk"):
            storage.retrieve("some-uuid")

    def test_delete_removes_file_and_row(self, storage, db, tmp_path):
        (tmp_path / "del.jpg").write_bytes(FAKE_BYTES)
        mock_image = Mock()
        mock_image.storage_ref = "del.jpg"
        db.exec = Mock(return_value=Mock(first=Mock(return_value=mock_image)))

        storage.delete("some-uuid")
        assert not (tmp_path / "del.jpg").exists()
        db.delete.assert_called_once_with(mock_image)

    def test_get_serving_url(self, storage):
        url = storage.get_serving_url("abc-123")
        assert url == "/api/v1/images/abc-123"


# ──────────────────────────────────────────────────────────────────────────────
# S3Storage (stub)
# ──────────────────────────────────────────────────────────────────────────────

class TestS3Storage:
    def test_store_raises(self):
        s = S3Storage()
        with pytest.raises(NotImplementedError, match="S3 storage backend"):
            s.store(b"x", "f.jpg", "image/jpeg")

    def test_retrieve_raises(self):
        s = S3Storage()
        with pytest.raises(NotImplementedError, match="S3 storage backend"):
            s.retrieve("x")

    def test_delete_raises(self):
        s = S3Storage()
        with pytest.raises(NotImplementedError, match="S3 storage backend"):
            s.delete("x")

    def test_get_serving_url_raises(self):
        s = S3Storage()
        with pytest.raises(NotImplementedError, match="S3 storage backend"):
            s.get_serving_url("x")


# ──────────────────────────────────────────────────────────────────────────────
# create_storage_backend factory
# ──────────────────────────────────────────────────────────────────────────────

class TestCreateStorageBackend:
    def test_returns_database_storage(self):
        mock_settings = Mock(IMAGE_STORAGE_BACKEND="database", API_V1_STR="/api/v1")
        backend = create_storage_backend(Mock(), mock_settings)
        assert isinstance(backend, DatabaseStorage)

    def test_returns_filesystem_storage(self, tmp_path):
        mock_settings = Mock(
            IMAGE_STORAGE_BACKEND="filesystem",
            IMAGE_STORAGE_PATH=str(tmp_path),
            API_V1_STR="/api/v1",
        )
        backend = create_storage_backend(Mock(), mock_settings)
        assert isinstance(backend, FileSystemStorage)

    def test_returns_s3_storage(self):
        mock_settings = Mock(IMAGE_STORAGE_BACKEND="s3")
        backend = create_storage_backend(Mock(), mock_settings)
        assert isinstance(backend, S3Storage)

    def test_raises_for_unknown_backend(self):
        mock_settings = Mock(IMAGE_STORAGE_BACKEND="unknown")
        with pytest.raises(ValueError, match="Unknown storage backend"):
            create_storage_backend(Mock(), mock_settings)
