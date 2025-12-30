"""AI-related API endpoints for LLM interactions."""

from fastapi import APIRouter, HTTPException, status, Depends
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
from src.core.config import settings
from openai import AuthenticationError, RateLimitError, APIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


def get_ai_service() -> AIService:
    """Dependency to get AI service instance."""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured. Please contact administrator."
        )
    
    return AIService(
        api_key=settings.OPENAI_API_KEY,
        org_id=settings.OPENAI_ORG_ID,
        default_model=settings.OPENAI_DEFAULT_MODEL,
        default_temperature=settings.OPENAI_TEMPERATURE,
        default_max_tokens=settings.OPENAI_MAX_TOKENS
    )


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
    request: AITestRequest,
    ai_service: Annotated[AIService, Depends(get_ai_service)]
):
    """
    Test endpoint for making LLM calls with custom prompts.
    This endpoint is intended for admin testing and development.
    
    Args:
        request: Test request with model, prompts, and parameters
        ai_service: AI service dependency
        
    Returns:
        LLM response with token usage and estimated cost
        
    Raises:
        HTTPException: If API call fails or service unavailable
    """
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
            detail=f"AI service error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in AI test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/suggest-tags", response_model=TagSuggestionResponse)
async def suggest_recipe_tags(
    request: TagSuggestionRequest,
    ai_service: Annotated[AIService, Depends(get_ai_service)]
):
    """
    Suggest relevant tags for a recipe based on its title and ingredients.
    
    Args:
        request: Recipe information (title, ingredients, existing tags)
        ai_service: AI service dependency
        
    Returns:
        List of suggested tag names with confidence score
        
    Raises:
        HTTPException: If API call fails
    """
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
    request: NaturalLanguageSearchRequest,
    ai_service: Annotated[AIService, Depends(get_ai_service)]
):
    """
    Convert a natural language query into structured search parameters.
    
    Args:
        request: Natural language search query
        ai_service: AI service dependency
        
    Returns:
        Structured search parameters (keywords, tags, filters)
        
    Raises:
        HTTPException: If parsing fails
    """
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
    request: NutritionRequest,
    ai_service: Annotated[AIService, Depends(get_ai_service)]
):
    """
    Calculate estimated nutrition facts for a recipe based on ingredients.
    
    Args:
        request: List of ingredients with amounts
        ai_service: AI service dependency
        
    Returns:
        Estimated nutrition facts per serving
        
    Raises:
        HTTPException: If calculation fails
    """
    try:
        logger.info(f"Calculating nutrition for {len(request.ingredients)} ingredients")
        
        ingredients_dict = [{"name": ing.name, "amount": ing.amount} for ing in request.ingredients]
        nutrition = await ai_service.calculate_nutrition(ingredients_dict)
        
        return NutritionResponse(**nutrition)
        
    except Exception as e:
        logger.error(f"Error calculating nutrition: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to calculate nutrition facts"
        )

