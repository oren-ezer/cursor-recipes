"""Tests for LLM Configuration model."""
import pytest
from src.models.llm_config import LLMConfig, LLMConfigType, LLMProvider
import uuid


def test_llm_config_model_instantiation():
    """Test creating an LLM configuration instance."""
    config = LLMConfig(
        uuid=str(uuid.uuid4()),
        config_type=LLMConfigType.GLOBAL,
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1000,
        created_by="test-admin-uuid"
    )
    
    assert config.config_type == LLMConfigType.GLOBAL
    assert config.provider == LLMProvider.OPENAI
    assert config.model == "gpt-4o-mini"
    assert config.temperature == 0.7
    assert config.max_tokens == 1000
    assert config.is_active is True
    assert config.service_name is None


def test_llm_config_service_specific():
    """Test creating a service-specific configuration."""
    config = LLMConfig(
        uuid=str(uuid.uuid4()),
        config_type=LLMConfigType.SERVICE,
        service_name="nutrition_calculation",
        provider=LLMProvider.OPENAI,
        model="gpt-4o",
        temperature=0.3,
        max_tokens=500,
        system_prompt="You are a nutrition expert.",
        response_format="json",
        created_by="test-admin-uuid",
        description="Config for nutrition calculations"
    )
    
    assert config.config_type == LLMConfigType.SERVICE
    assert config.service_name == "nutrition_calculation"
    assert config.system_prompt == "You are a nutrition expert."
    assert config.response_format == "json"
    assert config.description == "Config for nutrition calculations"


def test_llm_config_enum_values():
    """Test that enum values are correct."""
    assert LLMConfigType.GLOBAL.value == "GLOBAL"
    assert LLMConfigType.SERVICE.value == "SERVICE"
    
    assert LLMProvider.OPENAI.value == "OPENAI"
    assert LLMProvider.ANTHROPIC.value == "ANTHROPIC"
    assert LLMProvider.GOOGLE.value == "GOOGLE"


def test_llm_config_with_prompt_template():
    """Test configuration with prompt template."""
    config = LLMConfig(
        uuid=str(uuid.uuid4()),
        config_type=LLMConfigType.SERVICE,
        service_name="tag_suggestion",
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        temperature=0.5,
        max_tokens=500,
        system_prompt="You are a recipe tagger.",
        user_prompt_template="Recipe: {recipe_title}\nIngredients: {ingredients}\nSuggest tags.",
        created_by="test-admin"
    )
    
    assert "{recipe_title}" in config.user_prompt_template
    assert "{ingredients}" in config.user_prompt_template


def test_llm_config_defaults():
    """Test default values."""
    config = LLMConfig(
        uuid=str(uuid.uuid4()),
        created_by="test-admin"
    )
    
    assert config.config_type == LLMConfigType.GLOBAL
    assert config.provider == LLMProvider.OPENAI
    assert config.model == "gpt-4o-mini"
    assert config.temperature == 0.7
    assert config.max_tokens == 1000
    assert config.is_active is True
    assert config.system_prompt is None
    assert config.user_prompt_template is None


