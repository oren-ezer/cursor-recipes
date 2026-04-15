"""AI-related API endpoints for LLM interactions.

All AI endpoints require authentication (Bearer token).
The /test endpoint is restricted to superusers.
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends
from typing import Annotated
import logging

from src.models.ai_models import (
    AITestRequest,
    AITestResponse,
    TagSuggestionRequest,
    TagSuggestionResponse,
    NaturalLanguageSearchRequest,
    NaturalLanguageSearchResponse,
    NutritionRequest,
    NutritionResponse
)
from src.services.ai_service import AIService
from src.services.llm_config_service import LLMConfigService
from src.core.config import settings
from src.utils.database_session import get_db
from sqlmodel import Session
from openai import AuthenticationError, RateLimitError, APIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


def _require_auth(request: Request) -> dict:
    """Extract and validate the authenticated user from the request."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


def _require_admin(request: Request) -> dict:
    """Require an authenticated superuser."""
    user = _require_auth(request)
    if not user.get("is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )
    return user


def get_ai_service(db: Annotated[Session, Depends(get_db)]) -> AIService:
    """Dependency to get AI service instance."""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured. Please contact administrator."
        )
    
    llm_config_service = LLMConfigService(db)
    return AIService(db=db, llm_config_service=llm_config_service)


def calculate_cost(tokens: dict, model: str) -> float:
    """
    Calculate estimated cost based on token usage and model.
    
    Pricing as of Dec 2024 (per 1M tokens):
    - gpt-4o: $2.50 input, $10.00 output
    - gpt-4o-mini: $0.150 input, $0.600 output
    - gpt-3.5-turbo: $0.50 input, $1.50 output
    """
    pricing = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.150, "output": 0.600},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50}
    }
    
    # Default to gpt-4o-mini pricing if model not found
    model_pricing = pricing.get(model, pricing["gpt-4o-mini"])
    
    prompt_cost = (tokens["prompt"] / 1_000_000) * model_pricing["input"]
    completion_cost = (tokens["completion"] / 1_000_000) * model_pricing["output"]
    
    return round(prompt_cost + completion_cost, 6)


@router.post("/test", response_model=AITestResponse)
async def test_llm_call(
    http_request: Request,
    request: AITestRequest,
    ai_service: Annotated[AIService, Depends(get_ai_service)]
):
    """
    Test endpoint for making LLM calls with custom prompts.
    Restricted to administrators.
    """
    _require_admin(http_request)
    try:
        logger.info(f"Testing LLM call with model={request.model}")
        
        # Make the LLM call
        response = await ai_service.call_llm(
            user_prompt=request.user_prompt,
            system_prompt=request.system_prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format=request.response_format
        )
        
        # Calculate estimated cost
        estimated_cost = calculate_cost(response["tokens_used"], response["model"])
        
        return AITestResponse(
            content=response["content"],
            tokens_used=response["tokens_used"],
            model=response["model"],
            finish_reason=response["finish_reason"],
            estimated_cost=estimated_cost
        )
        
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service authentication failed. Please check API key configuration."
        )
    except RateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI service rate limit exceeded. Please try again later."
        )
    except APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in AI test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/suggest-tags", response_model=TagSuggestionResponse)
async def suggest_recipe_tags(
    http_request: Request,
    request: TagSuggestionRequest,
    ai_service: Annotated[AIService, Depends(get_ai_service)]
):
    """Suggest relevant tags for a recipe based on its title and ingredients."""
    _require_auth(http_request)
    try:
        logger.info(f"Suggesting tags for recipe: {request.recipe_title}")
        
        suggested_tags = await ai_service.suggest_tags(
            recipe_title=request.recipe_title,
            ingredients=request.ingredients,
            existing_tags=request.existing_tags
        )
        
        # Calculate confidence based on number of suggestions
        confidence = min(1.0, len(suggested_tags) / 5.0)
        
        return TagSuggestionResponse(
            suggested_tags=suggested_tags,
            confidence=confidence
        )
        
    except Exception as e:
        logger.error(f"Error suggesting tags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to generate tag suggestions"
        )


@router.post("/search", response_model=NaturalLanguageSearchResponse)
async def natural_language_search(
    http_request: Request,
    request: NaturalLanguageSearchRequest,
    ai_service: Annotated[AIService, Depends(get_ai_service)]
):
    """Convert a natural language query into structured search parameters."""
    _require_auth(http_request)
    try:
        logger.info(f"Parsing search query: {request.query}")
        
        search_params = await ai_service.parse_natural_language_search(request.query)
        
        return NaturalLanguageSearchResponse(**search_params)
        
    except Exception as e:
        logger.error(f"Error parsing search query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to parse search query"
        )


@router.post("/nutrition", response_model=NutritionResponse)
async def calculate_nutrition(
    http_request: Request,
    request: NutritionRequest,
    ai_service: Annotated[AIService, Depends(get_ai_service)]
):
    """Calculate estimated nutrition facts for a recipe based on ingredients."""
    _require_auth(http_request)
    try:
        logger.info(f"Calculating nutrition for {len(request.ingredients)} ingredients")
        
        ingredients_dict = [{"name": ing.name, "amount": ing.amount} for ing in request.ingredients]
        nutrition = await ai_service.calculate_nutrition(ingredients_dict, servings=request.servings)
        
        return NutritionResponse(**nutrition)
        
    except Exception as e:
        logger.error(f"Error calculating nutrition: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to calculate nutrition facts"
        )

