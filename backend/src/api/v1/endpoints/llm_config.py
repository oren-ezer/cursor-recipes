"""
LLM Configuration Management API Endpoints (Admin Only)

Provides CRUD operations for LLM configurations with proper authorization.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated, Dict, Any

from src.utils.dependencies import get_database_session, get_current_user
from src.services.llm_config_service import LLMConfigService
from src.models.llm_config import LLMConfig, LLMConfigType, LLMProvider


router = APIRouter(prefix="/llm-configs", tags=["LLM Configuration (Admin)"])


# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class LLMConfigBase(BaseModel):
    """Base fields for LLM configuration."""
    config_type: LLMConfigType
    service_name: Optional[str] = None
    provider: LLMProvider
    model: str
    temperature: float = Field(ge=0.0, le=2.0)
    max_tokens: int = Field(ge=1, le=4000)
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    response_format: Optional[str] = None
    description: Optional[str] = None


class LLMConfigCreate(LLMConfigBase):
    """Request model for creating a new LLM configuration."""
    pass


class LLMConfigUpdate(BaseModel):
    """Request model for updating an existing LLM configuration."""
    model_config = ConfigDict(extra='forbid')
    
    config_type: Optional[LLMConfigType] = None
    service_name: Optional[str] = None
    provider: Optional[LLMProvider] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    response_format: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class LLMConfigResponse(BaseModel):
    """Response model for LLM configuration."""
    id: int
    uuid: str
    config_type: str
    service_name: Optional[str]
    provider: str
    model: str
    temperature: float
    max_tokens: int
    system_prompt: Optional[str]
    user_prompt_template: Optional[str]
    response_format: Optional[str]
    is_active: bool
    created_by: str
    created_at: str
    updated_at: str
    description: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class EffectiveConfigResponse(BaseModel):
    """Response model for effective configuration with cascaded values."""
    provider: str
    model: str
    temperature: float
    max_tokens: int
    system_prompt: Optional[str]
    user_prompt_template: Optional[str]
    response_format: Optional[str]
    
    # Metadata about where each value came from
    source: dict = Field(
        default_factory=dict,
        description="Shows which config level each value came from"
    )


# ============================================================================
# Dependency for Admin Authorization
# ============================================================================

def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Verify that the current user is a superuser (admin)."""
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_llm_config_service(db: Annotated[Session, Depends(get_database_session)]) -> LLMConfigService:
    """Dependency to get LLMConfigService instance."""
    return LLMConfigService(db)


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/", response_model=List[LLMConfigResponse])
async def get_all_configs(
    admin: Dict[str, Any] = Depends(get_admin_user),
    service: LLMConfigService = Depends(get_llm_config_service)
):
    """
    Get all LLM configurations (admin only).
    
    Returns both global and service-specific configurations.
    """
    configs = service.get_all_configs()
    return [
        LLMConfigResponse(
            id=config.id,
            uuid=config.uuid,
            config_type=config.config_type.value,
            service_name=config.service_name,
            provider=config.provider.value,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            system_prompt=config.system_prompt,
            user_prompt_template=config.user_prompt_template,
            response_format=config.response_format,
            is_active=config.is_active,
            created_by=config.created_by,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat(),
            description=config.description
        )
        for config in configs
    ]


@router.get("/global", response_model=Optional[LLMConfigResponse])
async def get_global_config(
    admin: Dict[str, Any] = Depends(get_admin_user),
    service: LLMConfigService = Depends(get_llm_config_service)
):
    """
    Get the active global LLM configuration (admin only).
    
    Returns None if no global config exists.
    """
    config = service.get_global_config()
    if not config:
        return None
    
    return LLMConfigResponse(
        id=config.id,
        uuid=config.uuid,
        config_type=config.config_type.value,
        service_name=config.service_name,
        provider=config.provider.value,
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        system_prompt=config.system_prompt,
        user_prompt_template=config.user_prompt_template,
        response_format=config.response_format,
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
        description=config.description
    )


@router.get("/service/{service_name}", response_model=Optional[LLMConfigResponse])
async def get_service_config(
    service_name: str,
    admin: Dict[str, Any] = Depends(get_admin_user),
    service: LLMConfigService = Depends(get_llm_config_service)
):
    """
    Get the configuration for a specific service (admin only).
    
    Returns None if no service-specific config exists.
    """
    config = service.get_service_config(service_name)
    if not config:
        return None
    
    return LLMConfigResponse(
        id=config.id,
        uuid=config.uuid,
        config_type=config.config_type.value,
        service_name=config.service_name,
        provider=config.provider.value,
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        system_prompt=config.system_prompt,
        user_prompt_template=config.user_prompt_template,
        response_format=config.response_format,
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
        description=config.description
    )


@router.get("/effective/{service_name}", response_model=EffectiveConfigResponse)
async def get_effective_config(
    service_name: str,
    admin: Dict[str, Any] = Depends(get_admin_user),
    service: LLMConfigService = Depends(get_llm_config_service)
):
    """
    Get the effective configuration for a service after applying cascade (admin only).
    
    Shows the final configuration that would be used, with all fallbacks applied.
    """
    config = service.get_effective_config(service_name)
    
    return EffectiveConfigResponse(
        provider=config.get("provider"),
        model=config.get("model"),
        temperature=config.get("temperature"),
        max_tokens=config.get("max_tokens"),
        system_prompt=config.get("system_prompt"),
        user_prompt_template=config.get("user_prompt_template"),
        response_format=config.get("response_format"),
        source={
            "info": "Cascaded from: environment vars → global DB → service DB"
        }
    )


@router.post("/", response_model=LLMConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    config_data: LLMConfigCreate,
    admin: Dict[str, Any] = Depends(get_admin_user),
    service: LLMConfigService = Depends(get_llm_config_service)
):
    """
    Create a new LLM configuration (admin only).
    
    Validates that:
    - SERVICE type configs must have a service_name
    - GLOBAL type configs must not have a service_name
    """
    # Validation
    if config_data.config_type == LLMConfigType.SERVICE and not config_data.service_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="service_name is required for SERVICE type configurations"
        )
    
    if config_data.config_type == LLMConfigType.GLOBAL and config_data.service_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="service_name must be null for GLOBAL type configurations"
        )
    
    try:
        config = service.create_config(
            admin_uuid=admin["uuid"],
            config_data=config_data.model_dump()
        )
        
        return LLMConfigResponse(
            id=config.id,
            uuid=config.uuid,
            config_type=config.config_type.value,
            service_name=config.service_name,
            provider=config.provider.value,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            system_prompt=config.system_prompt,
            user_prompt_template=config.user_prompt_template,
            response_format=config.response_format,
            is_active=config.is_active,
            created_by=config.created_by,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat(),
            description=config.description
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create configuration: {str(e)}"
        )


@router.patch("/{config_id}", response_model=LLMConfigResponse)
async def update_config(
    config_id: int,
    update_data: LLMConfigUpdate,
    admin: Dict[str, Any] = Depends(get_admin_user),
    service: LLMConfigService = Depends(get_llm_config_service)
):
    """
    Update an existing LLM configuration (admin only).
    
    Only provided fields will be updated.
    """
    try:
        # Filter out None values
        update_dict = {
            k: v for k, v in update_data.model_dump().items() 
            if v is not None
        }
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update"
            )
        
        config = service.update_config(config_id, update_dict)
        
        return LLMConfigResponse(
            id=config.id,
            uuid=config.uuid,
            config_type=config.config_type.value,
            service_name=config.service_name,
            provider=config.provider.value,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            system_prompt=config.system_prompt,
            user_prompt_template=config.user_prompt_template,
            response_format=config.response_format,
            is_active=config.is_active,
            created_by=config.created_by,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat(),
            description=config.description
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    config_id: int,
    admin: Dict[str, Any] = Depends(get_admin_user),
    service: LLMConfigService = Depends(get_llm_config_service)
):
    """
    Delete an LLM configuration permanently (admin only).
    
    Removes the configuration record from the database.
    """
    try:
        service.delete_config(config_id)
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete configuration: {str(e)}"
        )

