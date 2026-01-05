"""Service for managing LLM configurations."""
from sqlmodel import Session, select
from src.models.llm_config import LLMConfig, LLMConfigType
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid as uuid_lib


class LLMConfigService:
    """Service for CRUD operations and configuration resolution for LLM configs."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_configs(self) -> List[LLMConfig]:
        """Get all LLM configurations."""
        statement = select(LLMConfig).order_by(LLMConfig.created_at.desc())
        return list(self.db.exec(statement).all())
    
    def get_active_configs(self) -> List[LLMConfig]:
        """Get all active LLM configurations."""
        statement = select(LLMConfig).where(
            LLMConfig.is_active == True
        ).order_by(LLMConfig.created_at.desc())
        return list(self.db.exec(statement).all())
    
    def get_global_config(self) -> Optional[LLMConfig]:
        """
        Get active global configuration.
        This serves as the system-wide default fallback.
        """
        statement = select(LLMConfig).where(
            LLMConfig.config_type == LLMConfigType.GLOBAL,
            LLMConfig.is_active == True
        )
        return self.db.exec(statement).first()
    
    def get_service_config(self, service_name: str) -> Optional[LLMConfig]:
        """
        Get configuration for specific service.
        
        Args:
            service_name: Name of the service (e.g., "tag_suggestion", "nutrition")
            
        Returns:
            LLMConfig if found, None otherwise
        """
        statement = select(LLMConfig).where(
            LLMConfig.config_type == LLMConfigType.SERVICE,
            LLMConfig.service_name == service_name,
            LLMConfig.is_active == True
        )
        return self.db.exec(statement).first()
    
    def get_config_by_id(self, config_id: int) -> Optional[LLMConfig]:
        """Get configuration by ID."""
        return self.db.get(LLMConfig, config_id)
    
    def get_config_by_uuid(self, config_uuid: str) -> Optional[LLMConfig]:
        """Get configuration by UUID."""
        statement = select(LLMConfig).where(LLMConfig.uuid == config_uuid)
        return self.db.exec(statement).first()
    
    def get_effective_config(
        self, 
        service_name: str,
        override_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get effective configuration with fallback hierarchy.
        
        Priority (highest to lowest):
        1. Runtime overrides (override_params)
        2. Service-specific config
        3. Global config
        4. Environment variable defaults
        
        Args:
            service_name: Name of the service requesting configuration
            override_params: Optional runtime parameter overrides
            
        Returns:
            Dictionary with effective configuration parameters
        """
        # Start with global defaults (fallback if no DB config exists)
        global_config = self.get_global_config()
        if global_config:
            config = self._config_to_dict(global_config)
        else:
            # Final fallback to environment variables
            config = self._get_env_defaults()
        
        # Override with service-specific config if exists
        service_config = self.get_service_config(service_name)
        if service_config:
            service_dict = self._config_to_dict(service_config)
            # Only override non-None values from service config
            config.update({k: v for k, v in service_dict.items() if v is not None})
        
        # Apply runtime overrides (highest priority)
        if override_params:
            config.update({k: v for k, v in override_params.items() if v is not None})
        
        return config
    
    def create_config(
        self,
        admin_uuid: str,
        config_data: Dict[str, Any]
    ) -> LLMConfig:
        """
        Create new LLM configuration.
        
        Args:
            admin_uuid: UUID of admin user creating the config
            config_data: Configuration parameters
            
        Returns:
            Created LLMConfig
            
        Raises:
            ValueError: If validation fails
        """
        # Generate UUID for new config
        new_uuid = str(uuid_lib.uuid4())
        
        # Create config instance
        config = LLMConfig(
            uuid=new_uuid,
            created_by=admin_uuid,
            **config_data
        )
        
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def update_config(
        self,
        config_id: int,
        update_data: Dict[str, Any]
    ) -> LLMConfig:
        """
        Update existing configuration.
        
        Args:
            config_id: ID of config to update
            update_data: Fields to update
            
        Returns:
            Updated LLMConfig
            
        Raises:
            ValueError: If config not found
        """
        config = self.db.get(LLMConfig, config_id)
        if not config:
            raise ValueError(f"Config with ID {config_id} not found")
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(config, key) and key not in ['id', 'uuid', 'created_by', 'created_at']:
                setattr(config, key, value)
        
        # Update timestamp
        config.updated_at = datetime.utcnow()
        
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def delete_config(self, config_id: int) -> None:
        """
        Hard delete (permanently remove) configuration.
        
        Args:
            config_id: ID of config to delete
            
        Raises:
            ValueError: If config not found
        """
        config = self.db.get(LLMConfig, config_id)
        if not config:
            raise ValueError(f"Config with ID {config_id} not found")
        
        self.db.delete(config)
        self.db.commit()
    
    def activate_config(self, config_id: int) -> LLMConfig:
        """
        Reactivate a previously deactivated configuration.
        
        Args:
            config_id: ID of config to activate
            
        Returns:
            Activated LLMConfig
            
        Raises:
            ValueError: If config not found
        """
        config = self.db.get(LLMConfig, config_id)
        if not config:
            raise ValueError(f"Config with ID {config_id} not found")
        
        config.is_active = True
        config.updated_at = datetime.utcnow()
        
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def _config_to_dict(self, config: LLMConfig) -> Dict[str, Any]:
        """
        Convert config model to dictionary.
        
        Args:
            config: LLMConfig instance
            
        Returns:
            Dictionary with config parameters
        """
        return {
            "provider": config.provider.value,
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "system_prompt": config.system_prompt,
            "user_prompt_template": config.user_prompt_template,
            "response_format": config.response_format,
        }
    
    def _get_env_defaults(self) -> Dict[str, Any]:
        """
        Get default configuration from environment variables.
        Final fallback if no database config exists.
        
        Returns:
            Dictionary with default config parameters
        """
        from src.core.config import settings
        return {
            "provider": "OPENAI",
            "model": settings.OPENAI_DEFAULT_MODEL,
            "temperature": settings.OPENAI_TEMPERATURE,
            "max_tokens": settings.OPENAI_MAX_TOKENS,
            "system_prompt": None,
            "user_prompt_template": None,
            "response_format": None,
        }

