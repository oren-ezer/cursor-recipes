"""Tests for LLMConfigService."""
import pytest
from src.services.llm_config_service import LLMConfigService
from src.models.llm_config import LLMConfig, LLMConfigType, LLMProvider
import uuid


def test_get_effective_config_with_global_only():
    """Test configuration resolution with only global config."""
    # This test doesn't use database, just tests the dict conversion logic
    service = LLMConfigService(None)  # type: ignore
    
    # Mock the methods to return test data
    global_config = LLMConfig(
        uuid=str(uuid.uuid4()),
        config_type=LLMConfigType.GLOBAL,
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1000,
        system_prompt="Global prompt",
        created_by="test"
    )
    
    service.get_global_config = lambda: global_config  # type: ignore
    service.get_service_config = lambda name: None  # type: ignore
    
    # Get effective config for a service with no specific config
    config = service.get_effective_config("some_service")
    
    # Should use global config
    assert config["model"] == "gpt-4o-mini"
    assert config["temperature"] == 0.7
    assert config["max_tokens"] == 1000
    assert config["system_prompt"] == "Global prompt"


def test_get_effective_config_with_service_override():
    """Test that service config overrides global config."""
    service = LLMConfigService(None)  # type: ignore
    
    # Mock global config
    global_config = LLMConfig(
        uuid=str(uuid.uuid4()),
        config_type=LLMConfigType.GLOBAL,
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1000,
        system_prompt="Global prompt",
        created_by="test"
    )
    
    # Mock service-specific config with different values
    service_config = LLMConfig(
        uuid=str(uuid.uuid4()),
        config_type=LLMConfigType.SERVICE,
        service_name="tag_suggestion",
        provider=LLMProvider.OPENAI,
        model="gpt-4o",  # Different model
        temperature=0.5,  # Different temperature
        max_tokens=500,  # Different max_tokens
        system_prompt="Tag suggestion prompt",  # Different prompt
        response_format="json",
        created_by="test"
    )
    
    service.get_global_config = lambda: global_config  # type: ignore
    service.get_service_config = lambda name: service_config if name == "tag_suggestion" else None  # type: ignore
    
    # Get effective config for tag_suggestion service
    config = service.get_effective_config("tag_suggestion")
    
    # Should use service config (overrides global)
    assert config["model"] == "gpt-4o"
    assert config["temperature"] == 0.5
    assert config["max_tokens"] == 500
    assert config["system_prompt"] == "Tag suggestion prompt"
    assert config["response_format"] == "json"


def test_get_effective_config_with_runtime_override():
    """Test that runtime overrides have highest priority."""
    service = LLMConfigService(None)  # type: ignore
    
    # Mock configs
    global_config = LLMConfig(
        uuid=str(uuid.uuid4()),
        config_type=LLMConfigType.GLOBAL,
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1000,
        created_by="test"
    )
    
    service_config = LLMConfig(
        uuid=str(uuid.uuid4()),
        config_type=LLMConfigType.SERVICE,
        service_name="nutrition",
        provider=LLMProvider.OPENAI,
        model="gpt-4o",
        temperature=0.3,
        max_tokens=500,
        created_by="test"
    )
    
    service.get_global_config = lambda: global_config  # type: ignore
    service.get_service_config = lambda name: service_config if name == "nutrition" else None  # type: ignore
    
    # Get effective config with runtime overrides
    config = service.get_effective_config(
        "nutrition",
        override_params={
            "temperature": 0.9,  # Override service temp
            "model": "gpt-4o-mini",  # Override service model
        }
    )
    
    # Runtime overrides should win
    assert config["model"] == "gpt-4o-mini"  # From runtime
    assert config["temperature"] == 0.9  # From runtime
    assert config["max_tokens"] == 500  # From service (not overridden)


def test_get_effective_config_cascade_hierarchy():
    """Test complete cascade: Global < Service < Runtime."""
    service = LLMConfigService(None)  # type: ignore
    
    # Global: all defaults
    global_config = LLMConfig(
        uuid=str(uuid.uuid4()),
        config_type=LLMConfigType.GLOBAL,
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1000,
        system_prompt="Global prompt",
        created_by="test"
    )
    
    # Service: overrides model and temperature
    service_config = LLMConfig(
        uuid=str(uuid.uuid4()),
        config_type=LLMConfigType.SERVICE,
        service_name="test_service",
        provider=LLMProvider.OPENAI,
        model="gpt-4o",  # Overrides global
        temperature=0.5,  # Overrides global
        max_tokens=None,  # Inherits from global
        system_prompt=None,  # Inherits from global
        created_by="test"
    )
    
    service.get_global_config = lambda: global_config  # type: ignore
    service.get_service_config = lambda name: service_config if name == "test_service" else None  # type: ignore
    
    # Runtime: overrides only temperature
    config = service.get_effective_config(
        "test_service",
        override_params={"temperature": 0.9}
    )
    
    # Check cascade:
    assert config["model"] == "gpt-4o"  # From service
    assert config["temperature"] == 0.9  # From runtime (highest priority)
    assert config["max_tokens"] == 1000  # From global (service didn't override)
    assert config["system_prompt"] == "Global prompt"  # From global


def test_config_to_dict_conversion():
    """Test conversion of LLMConfig to dict."""
    service = LLMConfigService(None)  # type: ignore
    
    config = LLMConfig(
        uuid=str(uuid.uuid4()),
        config_type=LLMConfigType.SERVICE,
        service_name="test",
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1000,
        system_prompt="Test prompt",
        user_prompt_template="Template: {recipe}",
        response_format="json",
        created_by="test"
    )
    
    result = service._config_to_dict(config)
    
    assert result["provider"] == "OPENAI"  # Enum value
    assert result["model"] == "gpt-4o-mini"
    assert result["temperature"] == 0.7
    assert result["max_tokens"] == 1000
    assert result["system_prompt"] == "Test prompt"
    assert result["user_prompt_template"] == "Template: {recipe}"
    assert result["response_format"] == "json"


def test_none_values_not_override():
    """Test that None values in override don't replace existing config."""
    service = LLMConfigService(None)  # type: ignore
    
    global_config = LLMConfig(
        uuid=str(uuid.uuid4()),
        config_type=LLMConfigType.GLOBAL,
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1000,
        system_prompt="Global prompt",
        created_by="test"
    )
    
    service.get_global_config = lambda: global_config  # type: ignore
    service.get_service_config = lambda name: None  # type: ignore
    
    # Override with None values - these should NOT replace existing values
    config = service.get_effective_config(
        "test_service",
        override_params={
            "model": None,  # Should not override
            "temperature": 0.9,  # Should override
        }
    )
    
    assert config["model"] == "gpt-4o-mini"  # Original value kept
    assert config["temperature"] == 0.9  # Overridden

