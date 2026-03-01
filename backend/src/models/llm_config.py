"""LLM Configuration model for managing AI service settings."""
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    GOOGLE = "GOOGLE"
    

class LLMConfigType(str, Enum):
    """Configuration scope types."""
    GLOBAL = "GLOBAL"      # System-wide defaults
    SERVICE = "SERVICE"    # Per-service overrides (e.g., "tag_suggestion", "nutrition")


class LLMConfig(SQLModel, table=True):
    """
    LLM Configuration model.
    
    Stores configuration for AI services with support for:
    - Global defaults
    - Service-specific overrides
    - Runtime parameter customization
    """
    __tablename__ = "llm_configs"
    
    # Primary identification
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(index=True, unique=True)
    
    # Configuration identification
    config_type: LLMConfigType = Field(default=LLMConfigType.GLOBAL)
    service_name: Optional[str] = Field(default=None, index=True)  # e.g., "tag_suggestion", "nutrition"
    
    # LLM Settings
    provider: LLMProvider = Field(default=LLMProvider.OPENAI)
    model: str = Field(default="gpt-4o-mini")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=4000)
    
    # Prompts (optional - use defaults if not set)
    system_prompt: Optional[str] = Field(default=None)
    user_prompt_template: Optional[str] = Field(default=None)  # Template with {placeholders}
    
    # Response format
    response_format: Optional[str] = Field(default=None)  # "text" or "json"
    
    # Metadata
    is_active: bool = Field(default=True)
    created_by: str = Field(index=True)  # UUID of admin user
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Description for admin reference
    description: Optional[str] = Field(default=None)
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "config_type": "SERVICE",
                "service_name": "tag_suggestion",
                "provider": "OPENAI",
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 500,
                "system_prompt": "You are a helpful culinary AI assistant.",
                "user_prompt_template": "Suggest tags for: {recipe_title}",
                "response_format": "json",
                "description": "Configuration for recipe tag suggestion service"
            }
        }

