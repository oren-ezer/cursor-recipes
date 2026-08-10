"""Registry of admin-editable application settings, grouped by purpose."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional

from src.core.config import settings

SettingType = Literal["string", "integer", "float", "enum"]


@dataclass(frozen=True)
class SettingDefinition:
    key: str
    group: str
    value_type: SettingType
    env_attr: str
    description: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    options: tuple[str, ...] = field(default_factory=tuple)
    validate: Optional[Callable[[Any], Any]] = None


def _default_from_env(env_attr: str) -> Any:
    return getattr(settings, env_attr)


SETTING_DEFINITIONS: List[SettingDefinition] = [
    # Application
    SettingDefinition(
        key="project_name",
        group="application",
        value_type="string",
        env_attr="PROJECT_NAME",
        description="Display name of the API / application",
    ),
    SettingDefinition(
        key="project_description",
        group="application",
        value_type="string",
        env_attr="PROJECT_DESCRIPTION",
        description="Short description shown in API docs",
    ),
    # Authentication
    SettingDefinition(
        key="access_token_expire_minutes",
        group="authentication",
        value_type="integer",
        env_attr="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="JWT access token lifetime in minutes",
        min_value=1,
        max_value=10080,
    ),
    # AI defaults (env fallback used by LLM config cascade)
    SettingDefinition(
        key="openai_default_model",
        group="ai_defaults",
        value_type="string",
        env_attr="OPENAI_DEFAULT_MODEL",
        description="Default model when no LLM config is set",
    ),
    SettingDefinition(
        key="openai_max_tokens",
        group="ai_defaults",
        value_type="integer",
        env_attr="OPENAI_MAX_TOKENS",
        description="Default max tokens for AI responses",
        min_value=1,
        max_value=16384,
    ),
    SettingDefinition(
        key="openai_temperature",
        group="ai_defaults",
        value_type="float",
        env_attr="OPENAI_TEMPERATURE",
        description="Default sampling temperature (0–2)",
        min_value=0.0,
        max_value=2.0,
    ),
    # Image uploads
    SettingDefinition(
        key="max_image_upload_size_mb",
        group="image_uploads",
        value_type="integer",
        env_attr="MAX_IMAGE_UPLOAD_SIZE_MB",
        description="Maximum size of a single uploaded image in MB",
        min_value=1,
        max_value=100,
    ),
    SettingDefinition(
        key="max_images_per_upload",
        group="image_uploads",
        value_type="integer",
        env_attr="MAX_IMAGES_PER_UPLOAD",
        description="Maximum number of images per upload request",
        min_value=1,
        max_value=50,
    ),
    SettingDefinition(
        key="image_storage_backend",
        group="image_uploads",
        value_type="enum",
        env_attr="IMAGE_STORAGE_BACKEND",
        description="Where uploaded images are stored",
        options=("database", "filesystem", "s3"),
    ),
    SettingDefinition(
        key="image_storage_path",
        group="image_uploads",
        value_type="string",
        env_attr="IMAGE_STORAGE_PATH",
        description="Filesystem path when using the filesystem backend",
    ),
]

SETTING_BY_KEY: Dict[str, SettingDefinition] = {d.key: d for d in SETTING_DEFINITIONS}

GROUP_ORDER = ("application", "authentication", "ai_defaults", "image_uploads")


def serialize_value(definition: SettingDefinition, value: Any) -> str:
    if definition.value_type == "float":
        return str(float(value))
    if definition.value_type == "integer":
        return str(int(value))
    return str(value)


def parse_value(definition: SettingDefinition, raw: str) -> Any:
    if definition.value_type == "integer":
        value: Any = int(raw)
    elif definition.value_type == "float":
        value = float(raw)
    else:
        value = str(raw).strip()

    if definition.value_type == "enum":
        if value not in definition.options:
            raise ValueError(
                f"Invalid value for {definition.key}: {value}. "
                f"Allowed: {', '.join(definition.options)}"
            )

    if definition.min_value is not None and value < definition.min_value:
        raise ValueError(
            f"{definition.key} must be >= {definition.min_value}"
        )
    if definition.max_value is not None and value > definition.max_value:
        raise ValueError(
            f"{definition.key} must be <= {definition.max_value}"
        )

    if definition.value_type == "string" and not value and definition.key != "project_description":
        raise ValueError(f"{definition.key} cannot be empty")

    if definition.validate:
        value = definition.validate(value)

    return value


def env_default(definition: SettingDefinition) -> Any:
    return _default_from_env(definition.env_attr)
