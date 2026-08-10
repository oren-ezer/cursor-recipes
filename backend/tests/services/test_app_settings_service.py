"""Tests for AppSettingsService and admin settings endpoints."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import status

from src.main import app
from src.core.config import settings
from src.models.app_setting import AppSetting
from src.services.app_settings_service import AppSettingsService
from src.utils.dependencies import get_app_settings_service, get_current_user


ADMINS_PREFIX = f"{settings.API_V1_STR}/admins"


def _admin_user():
    return {
        "id": 1,
        "uuid": "admin-uuid",
        "email": "admin@example.com",
        "is_superuser": True,
        "is_active": True,
    }


def _regular_user():
    return {
        "id": 2,
        "uuid": "user-uuid",
        "email": "user@example.com",
        "is_superuser": False,
        "is_active": True,
    }


class TestAppSettingsService:
    def test_falls_back_to_env_defaults(self):
        db = Mock()
        result = Mock()
        result.first = Mock(return_value=None)
        result.all = Mock(return_value=[])
        db.exec = Mock(return_value=result)

        service = AppSettingsService(db)
        with patch.object(settings, "MAX_IMAGE_UPLOAD_SIZE_MB", 12):
            assert service.get_int("max_image_upload_size_mb") == 12

    def test_uses_database_override(self):
        row = AppSetting(key="max_image_upload_size_mb", value="25")
        db = Mock()

        def exec_side_effect(statement):
            result = Mock()
            result.first = Mock(return_value=row)
            result.all = Mock(return_value=[row])
            return result

        db.exec = Mock(side_effect=exec_side_effect)
        service = AppSettingsService(db)
        assert service.get_int("max_image_upload_size_mb") == 25

    def test_update_settings_validates_enum(self):
        db = Mock()
        result = Mock()
        result.first = Mock(return_value=None)
        result.all = Mock(return_value=[])
        db.exec = Mock(return_value=result)

        service = AppSettingsService(db)
        with pytest.raises(ValueError, match="Invalid value"):
            service.update_settings({"image_storage_backend": "tape"})

    def test_grouped_settings_structure(self):
        db = Mock()
        result = Mock()
        result.first = Mock(return_value=None)
        result.all = Mock(return_value=[])
        db.exec = Mock(return_value=result)

        service = AppSettingsService(db)
        data = service.get_grouped_settings()
        group_ids = [g["id"] for g in data["groups"]]
        assert group_ids == [
            "application",
            "authentication",
            "ai_defaults",
            "image_uploads",
        ]
        assert "openai_api_key_configured" in data["status"]


@pytest.fixture
def client_with_settings():
    store: dict[str, AppSetting] = {}

    db = Mock()

    def exec_side_effect(statement):
        result = Mock()
        # Rough: if querying all, return values; first returns by last key pattern
        result.all = Mock(return_value=list(store.values()))

        def first():
            if not store:
                return None
            # Prefer returning None for single-key lookups when missing;
            # statement inspection is awkward with mocks — return matching if only one.
            return next(iter(store.values()), None) if len(store) == 1 else None

        result.first = Mock(side_effect=first)
        return result

    def add_side_effect(obj):
        if isinstance(obj, AppSetting):
            store[obj.key] = obj

    db.exec = Mock(side_effect=exec_side_effect)
    db.add = Mock(side_effect=add_side_effect)
    db.commit = Mock()

    # Use a more realistic service with in-memory store
    class MemoryAppSettingsService(AppSettingsService):
        def _load_overrides(self):
            return dict(store)

        def get_value(self, key):
            from src.core.app_settings_registry import SETTING_BY_KEY, env_default, parse_value

            definition = SETTING_BY_KEY[key]
            row = store.get(key)
            if row is None:
                return env_default(definition)
            return parse_value(definition, row.value)

        def update_settings(self, updates, updated_by=None):
            from datetime import datetime, timezone
            from src.core.app_settings_registry import (
                SETTING_BY_KEY,
                parse_value,
                serialize_value,
            )

            if not updates:
                raise ValueError("No settings provided")
            unknown = set(updates) - set(SETTING_BY_KEY)
            if unknown:
                raise ValueError(f"Unknown setting keys: {', '.join(sorted(unknown))}")

            now = datetime.now(timezone.utc)
            for key, raw_value in updates.items():
                definition = SETTING_BY_KEY[key]
                parsed = parse_value(definition, str(raw_value))
                stored = serialize_value(definition, parsed)
                existing = store.get(key)
                if existing is None:
                    store[key] = AppSetting(
                        key=key,
                        value=stored,
                        updated_by=updated_by,
                        created_at=now,
                        updated_at=now,
                    )
                else:
                    existing.value = stored
                    existing.updated_by = updated_by
                    existing.updated_at = now
            return self.get_grouped_settings()

    service = MemoryAppSettingsService(db)
    app.dependency_overrides[get_app_settings_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    with TestClient(app) as c:
        yield c, service
    app.dependency_overrides.pop(get_app_settings_service, None)
    app.dependency_overrides.pop(get_current_user, None)


class TestAdminSettingsEndpoints:
    def test_get_settings_requires_admin(self):
        app.dependency_overrides[get_current_user] = lambda: _regular_user()
        empty = Mock()
        empty_result = Mock()
        empty_result.first = Mock(return_value=None)
        empty_result.all = Mock(return_value=[])
        empty.exec = Mock(return_value=empty_result)
        app.dependency_overrides[get_app_settings_service] = (
            lambda: AppSettingsService(empty)
        )
        try:
            with TestClient(app) as client:
                resp = client.get(f"{ADMINS_PREFIX}/settings")
            assert resp.status_code == status.HTTP_403_FORBIDDEN
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_app_settings_service, None)

    def test_get_settings_grouped(self, client_with_settings):
        client, _ = client_with_settings
        resp = client.get(f"{ADMINS_PREFIX}/settings")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "groups" in body
        assert "status" in body
        assert len(body["groups"]) == 4

    def test_update_settings(self, client_with_settings):
        client, service = client_with_settings
        resp = client.put(
            f"{ADMINS_PREFIX}/settings",
            json={"settings": {"max_image_upload_size_mb": 15}},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert service.get_int("max_image_upload_size_mb") == 15
        image_group = next(g for g in resp.json()["groups"] if g["id"] == "image_uploads")
        size_setting = next(
            s for s in image_group["settings"] if s["key"] == "max_image_upload_size_mb"
        )
        assert size_setting["value"] == 15
        assert size_setting["source"] == "database"

    def test_update_rejects_unknown_key(self, client_with_settings):
        client, _ = client_with_settings
        resp = client.put(
            f"{ADMINS_PREFIX}/settings",
            json={"settings": {"not_a_real_key": 1}},
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
