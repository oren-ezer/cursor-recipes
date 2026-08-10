"""Service for reading and updating admin-editable app settings."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from src.core.app_settings_registry import (
    GROUP_ORDER,
    SETTING_BY_KEY,
    SETTING_DEFINITIONS,
    SettingDefinition,
    env_default,
    parse_value,
    serialize_value,
)
from src.core.config import settings
from src.models.app_setting import AppSetting


class AppSettingsService:
    def __init__(self, db: Session):
        self.db = db

    def _load_overrides(self) -> Dict[str, AppSetting]:
        rows = self.db.exec(select(AppSetting)).all()
        return {row.key: row for row in rows}

    def get_value(self, key: str) -> Any:
        definition = SETTING_BY_KEY.get(key)
        if not definition:
            raise KeyError(f"Unknown setting key: {key}")

        row = self.db.exec(select(AppSetting).where(AppSetting.key == key)).first()
        if row is None:
            return env_default(definition)
        return parse_value(definition, row.value)

    def get_int(self, key: str) -> int:
        return int(self.get_value(key))

    def get_float(self, key: str) -> float:
        return float(self.get_value(key))

    def get_str(self, key: str) -> str:
        return str(self.get_value(key))

    def get_image_upload_limits(self) -> Dict[str, int]:
        return {
            "max_file_size_mb": self.get_int("max_image_upload_size_mb"),
            "max_files_per_upload": self.get_int("max_images_per_upload"),
        }

    def get_storage_settings(self) -> SimpleNamespace:
        """Settings-like object for image storage factory."""
        return SimpleNamespace(
            IMAGE_STORAGE_BACKEND=self.get_str("image_storage_backend"),
            IMAGE_STORAGE_PATH=self.get_str("image_storage_path"),
            API_V1_STR=settings.API_V1_STR,
        )

    def get_grouped_settings(self) -> Dict[str, Any]:
        overrides = self._load_overrides()
        groups: List[Dict[str, Any]] = []

        for group_id in GROUP_ORDER:
            items: List[Dict[str, Any]] = []
            for definition in SETTING_DEFINITIONS:
                if definition.group != group_id:
                    continue
                items.append(self._to_setting_item(definition, overrides.get(definition.key)))
            groups.append({"id": group_id, "settings": items})

        return {
            "groups": groups,
            "status": self.get_integration_status(),
        }

    def _to_setting_item(
        self,
        definition: SettingDefinition,
        row: Optional[AppSetting],
    ) -> Dict[str, Any]:
        default = env_default(definition)
        if row is not None:
            value = parse_value(definition, row.value)
            source = "database"
        else:
            value = default
            source = "environment"

        return {
            "key": definition.key,
            "group": definition.group,
            "type": definition.value_type,
            "value": value,
            "default_value": default,
            "source": source,
            "description": definition.description,
            "min_value": definition.min_value,
            "max_value": definition.max_value,
            "options": list(definition.options) if definition.options else None,
            "updated_at": row.updated_at.isoformat() if row else None,
            "updated_by": row.updated_by if row else None,
        }

    def get_integration_status(self) -> Dict[str, bool]:
        return {
            "database_url_configured": bool(settings.DATABASE_URL),
            "supabase_url_configured": bool(settings.SUPABASE_URL),
            "supabase_key_configured": bool(settings.SUPABASE_KEY),
            "supabase_service_key_configured": bool(settings.SUPABASE_SERVICE_KEY),
            "openai_api_key_configured": bool(settings.OPENAI_API_KEY),
            "google_api_key_configured": bool(settings.GOOGLE_API_KEY),
            "anthropic_api_key_configured": bool(settings.ANTHROPIC_API_KEY),
            "secret_key_configured": bool(
                settings.SECRET_KEY and settings.SECRET_KEY != "your-secret-key-here"
            ),
        }

    def update_settings(
        self,
        updates: Dict[str, Any],
        updated_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not updates:
            raise ValueError("No settings provided")

        unknown = set(updates) - set(SETTING_BY_KEY)
        if unknown:
            raise ValueError(f"Unknown setting keys: {', '.join(sorted(unknown))}")

        now = datetime.now(timezone.utc)
        overrides = self._load_overrides()

        for key, raw_value in updates.items():
            definition = SETTING_BY_KEY[key]
            parsed = parse_value(definition, str(raw_value))
            stored = serialize_value(definition, parsed)

            existing = overrides.get(key)
            if existing is None:
                existing = AppSetting(
                    key=key,
                    value=stored,
                    updated_by=updated_by,
                    created_at=now,
                    updated_at=now,
                )
                self.db.add(existing)
            else:
                existing.value = stored
                existing.updated_by = updated_by
                existing.updated_at = now
                self.db.add(existing)

        self.db.commit()
        return self.get_grouped_settings()
