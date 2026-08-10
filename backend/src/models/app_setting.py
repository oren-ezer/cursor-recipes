"""App settings model for admin-editable configuration overrides."""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class AppSetting(SQLModel, table=True):
    """Key/value override stored in the database.

    Missing keys fall back to environment / Settings defaults.
    """

    __tablename__ = "app_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True, max_length=100)
    value: str = Field(max_length=2000)
    updated_by: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
