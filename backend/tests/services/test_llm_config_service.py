"""Tests for LLMConfigService."""
import pytest
from unittest.mock import Mock, patch
import uuid
from src.services.llm_config_service import LLMConfigService
from src.models.llm_config import LLMConfig, LLMConfigType, LLMProvider

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def service(mock_db):
    return LLMConfigService(mock_db)

@pytest.fixture
def global_config():
    return LLMConfig(
        id=1,
        uuid=str(uuid.uuid4()),
        config_type=LLMConfigType.GLOBAL,
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1000,
        system_prompt="Global prompt",
        created_by="test",
        is_active=True
    )

@pytest.fixture
def service_config():
    return LLMConfig(
        id=2,
        uuid=str(uuid.uuid4()),
        config_type=LLMConfigType.SERVICE,
        service_name="tag_suggestion",
        provider=LLMProvider.OPENAI,
        model="gpt-4o",
        temperature=0.5,
        max_tokens=500,
        system_prompt="Tag suggestion prompt",
        response_format="json",
        created_by="test",
        is_active=True
    )

def test_init(mock_db):
    svc = LLMConfigService(mock_db)
    assert svc.db == mock_db

def test_get_all_configs(service, mock_db, global_config, service_config):
    mock_result = Mock()
    mock_result.all.return_value = [global_config, service_config]
    mock_db.exec.return_value = mock_result
    
    configs = service.get_all_configs()
    
    assert len(configs) == 2
    assert configs[0] == global_config
    assert configs[1] == service_config
    mock_db.exec.assert_called_once()

def test_get_active_configs(service, mock_db, global_config):
    mock_result = Mock()
    mock_result.all.return_value = [global_config]
    mock_db.exec.return_value = mock_result
    
    configs = service.get_active_configs()
    
    assert len(configs) == 1
    assert configs[0] == global_config
    mock_db.exec.assert_called_once()

def test_get_global_config(service, mock_db, global_config):
    mock_result = Mock()
    mock_result.first.return_value = global_config
    mock_db.exec.return_value = mock_result
    
    config = service.get_global_config()
    
    assert config == global_config
    mock_db.exec.assert_called_once()

def test_get_service_config(service, mock_db, service_config):
    mock_result = Mock()
    mock_result.first.return_value = service_config
    mock_db.exec.return_value = mock_result
    
    config = service.get_service_config("tag_suggestion")
    
    assert config == service_config
    mock_db.exec.assert_called_once()

def test_get_config_by_id(service, mock_db, global_config):
    mock_db.get.return_value = global_config
    
    config = service.get_config_by_id(1)
    
    assert config == global_config
    mock_db.get.assert_called_once_with(LLMConfig, 1)

def test_get_config_by_uuid(service, mock_db, global_config):
    mock_result = Mock()
    mock_result.first.return_value = global_config
    mock_db.exec.return_value = mock_result
    
    config = service.get_config_by_uuid(global_config.uuid)
    
    assert config == global_config
    mock_db.exec.assert_called_once()

def test_create_config(service, mock_db):
    config_data = {
        "config_type": LLMConfigType.GLOBAL,
        "provider": LLMProvider.OPENAI,
        "model": "gpt-4",
    }
    
    with patch("src.services.llm_config_service.uuid_lib.uuid4") as mock_uuid:
        mock_uuid.return_value = "mocked-uuid"
        
        # We need to simulate db.refresh adding an ID
        def mock_add(obj):
            pass
            
        def mock_refresh(obj):
            obj.id = 1
            
        mock_db.add.side_effect = mock_add
        mock_db.refresh.side_effect = mock_refresh
        
        config = service.create_config("admin-uuid", config_data)
        
        assert config.uuid == "mocked-uuid"
        assert config.created_by == "admin-uuid"
        assert config.model == "gpt-4"
        assert config.id == 1
        
        mock_db.add.assert_called_once_with(config)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(config)

def test_update_config_success(service, mock_db, global_config):
    mock_db.get.return_value = global_config
    update_data = {"model": "gpt-4-turbo", "temperature": 0.1, "uuid": "dont-update", "non_existent": "ignore"}
    
    config = service.update_config(1, update_data)
    
    assert config.model == "gpt-4-turbo"
    assert config.temperature == 0.1
    # Check that protected fields weren't updated
    assert config.uuid != "dont-update"
    
    mock_db.add.assert_called_once_with(config)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(config)

def test_update_config_not_found(service, mock_db):
    mock_db.get.return_value = None
    
    with pytest.raises(ValueError, match="Config with ID 999 not found"):
        service.update_config(999, {"model": "gpt-4"})

def test_delete_config_success(service, mock_db, global_config):
    mock_db.get.return_value = global_config
    
    service.delete_config(1)
    
    mock_db.delete.assert_called_once_with(global_config)
    mock_db.commit.assert_called_once()

def test_delete_config_not_found(service, mock_db):
    mock_db.get.return_value = None
    
    with pytest.raises(ValueError, match="Config with ID 999 not found"):
        service.delete_config(999)

def test_activate_config_success(service, mock_db, global_config):
    global_config.is_active = False
    mock_db.get.return_value = global_config
    
    config = service.activate_config(1)
    
    assert config.is_active is True
    mock_db.add.assert_called_once_with(config)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(config)

def test_activate_config_not_found(service, mock_db):
    mock_db.get.return_value = None
    
    with pytest.raises(ValueError, match="Config with ID 999 not found"):
        service.activate_config(999)

def test_config_to_dict(service, global_config):
    result = service._config_to_dict(global_config)
    
    assert result["provider"] == "OPENAI"
    assert result["model"] == "gpt-4o-mini"
    assert result["temperature"] == 0.7
    assert result["max_tokens"] == 1000
    assert result["system_prompt"] == "Global prompt"
    assert result["user_prompt_template"] is None
    assert result["response_format"] is None

@patch("src.services.app_settings_service.AppSettingsService")
def test_get_env_defaults(mock_app_settings_cls, service):
    mock_app_settings = Mock()
    mock_app_settings_cls.return_value = mock_app_settings
    
    mock_app_settings.get_str.return_value = "gpt-4-env"
    mock_app_settings.get_float.return_value = 0.9
    mock_app_settings.get_int.return_value = 2000
    
    result = service._get_env_defaults()
    
    assert result["provider"] == "OPENAI"
    assert result["model"] == "gpt-4-env"
    assert result["temperature"] == 0.9
    assert result["max_tokens"] == 2000
    assert result["system_prompt"] is None
    
    mock_app_settings_cls.assert_called_once_with(service.db)
    mock_app_settings.get_str.assert_called_once_with("openai_default_model")
    mock_app_settings.get_float.assert_called_once_with("openai_temperature")
    mock_app_settings.get_int.assert_called_once_with("openai_max_tokens")

# --- Tests for get_effective_config ---

def test_get_effective_config_cascade_hierarchy(service, global_config, service_config):
    with patch.object(service, "get_global_config", return_value=global_config), \
         patch.object(service, "get_service_config", return_value=service_config):
        
        config = service.get_effective_config(
            "tag_suggestion",
            override_params={"temperature": 0.9}
        )
        
        # Check cascade: Service overrides global, runtime overrides service
        assert config["model"] == "gpt-4o"  # From service
        assert config["temperature"] == 0.9  # From runtime (highest priority)
        assert config["max_tokens"] == 500  # From service
        assert config["system_prompt"] == "Tag suggestion prompt"  # From service
        assert config["response_format"] == "json"  # From service

def test_get_effective_config_with_global_only(service, global_config):
    with patch.object(service, "get_global_config", return_value=global_config), \
         patch.object(service, "get_service_config", return_value=None):
        
        config = service.get_effective_config("tag_suggestion")
        
        # Should use global config
        assert config["model"] == "gpt-4o-mini"
        assert config["temperature"] == 0.7
        assert config["max_tokens"] == 1000
        assert config["system_prompt"] == "Global prompt"

def test_get_effective_config_fallback_to_env(service):
    with patch.object(service, "get_global_config", return_value=None), \
         patch.object(service, "get_service_config", return_value=None), \
         patch.object(service, "_get_env_defaults") as mock_env_defaults:
             
        mock_env_defaults.return_value = {
            "provider": "OPENAI",
            "model": "gpt-env",
            "temperature": 0.8,
            "max_tokens": 1500,
            "system_prompt": None,
            "user_prompt_template": None,
            "response_format": None,
        }
        
        config = service.get_effective_config("tag_suggestion")
        
        assert config["model"] == "gpt-env"
        assert config["temperature"] == 0.8
        assert config["max_tokens"] == 1500

def test_get_effective_config_none_values_dont_override(service, global_config, service_config):
    # Set a field in service_config to None to ensure it doesn't override global
    service_config.max_tokens = None
    
    with patch.object(service, "get_global_config", return_value=global_config), \
         patch.object(service, "get_service_config", return_value=service_config):
        
        config = service.get_effective_config(
            "tag_suggestion",
            override_params={"temperature": None}  # Should not override
        )
        
        # max_tokens should fall back to global because service has it as None
        assert config["max_tokens"] == 1000
        # temperature should be from service because runtime is None
        assert config["temperature"] == 0.5


