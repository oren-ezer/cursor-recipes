"""AI-related API endpoints for LLM interactions.

All AI endpoints require authentication (Bearer token).
The /test endpoint is restricted to superusers.
"""

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status, Depends
from typing import Annotated, List
import logging

from src.models.ai_models import (
    AITestRequest,
    AITestResponse,
    TagSuggestionRequest,
    TagSuggestionResponse,
    NaturalLanguageSearchRequest,
    NaturalLanguageSearchResponse,
    NutritionRequest,
    NutritionResponse,
    RecipeFromImageResponse,
    RecipeFromImageIngredient,
    MultiRecipeFromImageResponse,
)
from src.services.ai_service import AIService
from src.services.llm_config_service import LLMConfigService
from src.services.tag_service import TagService
from src.core.config import settings
from src.services.app_settings_service import AppSettingsService
from src.utils.database_session import get_db
from src.utils.dependencies import get_app_settings_service, get_tag_service
from sqlmodel import Session
from openai import AuthenticationError, RateLimitError, APIError
import base64

ALLOWED_PARSE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

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
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    tag_service: Annotated[TagService, Depends(get_tag_service)]
):
    """Suggest relevant tags for a recipe based on its title and ingredients."""
    _require_auth(http_request)
    try:
        logger.info(f"Suggesting tags for recipe: {request.recipe_title}")
        
        # Get all available tags to guide the LLM
        tags_response = tag_service.get_all_tags(limit=1000)
        all_tags = tags_response.get("tags", [])
        available_tags = [tag.name for tag in all_tags] if all_tags else None
        
        suggested_tags = await ai_service.suggest_tags(
            recipe_title=request.recipe_title,
            ingredients=request.ingredients,
            existing_tags=request.existing_tags,
            available_tags=available_tags
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


@router.post("/parse-recipe-images", response_model=MultiRecipeFromImageResponse)
async def parse_recipe_from_images(
    http_request: Request,
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    app_settings: Annotated[AppSettingsService, Depends(get_app_settings_service)],
    images: List[UploadFile] = File(..., description="Recipe image files to parse (not stored)"),
    language_hint: str = Form(
        ...,
        min_length=1,
        max_length=50,
        description="Language of the recipe text in the image (e.g. 'Hebrew', 'English')",
    ),
):
    """
    Extract recipe data from image files using AI vision.

    Accepts multipart image uploads in-memory only — files are NOT saved to
    recipe_images. After the user creates the recipe, the client can upload the
    same files via /images/upload with the new recipe_id.
    """
    _require_auth(http_request)

    language_hint = language_hint.strip()
    if not language_hint:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="language_hint is required",
        )

    if not images:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one image is required",
        )

    limits = app_settings.get_image_upload_limits()
    max_files = limits["max_files_per_upload"]
    max_size_mb = limits["max_file_size_mb"]

    if len(images) > max_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {max_files} images per request",
        )

    max_bytes = max_size_mb * 1024 * 1024
    image_data_uris: list[str] = []
    for upload in images:
        if upload.content_type not in ALLOWED_PARSE_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"File '{upload.filename}' has unsupported type '{upload.content_type}'. "
                    f"Allowed: {', '.join(sorted(ALLOWED_PARSE_CONTENT_TYPES))}"
                ),
            )
        file_bytes = await upload.read()
        if len(file_bytes) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"File '{upload.filename}' exceeds "
                    f"{max_size_mb} MB limit"
                ),
            )
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        image_data_uris.append(f"data:{upload.content_type};base64,{b64}")

    try:
        logger.info(f"Parsing recipe from {len(image_data_uris)} image(s)")

        results = await ai_service.parse_recipe_from_images(
            image_data_uris=image_data_uris,
            language_hint=language_hint,
        )

        recipes = []
        for result in results:
            raw_ingredients = result.get("ingredients", [])
            ingredients = []
            for ing in raw_ingredients:
                if isinstance(ing, dict):
                    ingredients.append(
                        RecipeFromImageIngredient(name=ing.get("name", ""), amount=ing.get("amount", ""))
                    )
                elif isinstance(ing, str):
                    ingredients.append(RecipeFromImageIngredient(name=ing, amount=""))

            raw_instructions = result.get("instructions", [])
            instructions = [
                step if isinstance(step, str) else str(step)
                for step in raw_instructions
            ]

            recipes.append(RecipeFromImageResponse(
                title=result.get("title", ""),
                description=result.get("description", ""),
                ingredients=ingredients,
                instructions=instructions,
                preparation_time=int(result.get("preparation_time", 30) or 30),
                cooking_time=int(result.get("cooking_time", 30) or 30),
                servings=int(result.get("servings", 4) or 4),
                difficulty_level=result.get("difficulty_level", "Easy") or "Easy",
            ))

        return MultiRecipeFromImageResponse(recipes=recipes)

    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service authentication failed. Please check API key configuration.",
        )
    except RateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI service rate limit exceeded. Please try again later.",
        )
    except APIError as e:
        logger.error(f"OpenAI API error during image parsing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable",
        )
    except Exception as e:
        logger.error(f"Unexpected error parsing recipe from images: {str(e)}", exc_info=True)
        message = str(e)
        # Surface common provider misconfiguration (e.g. invalid Gemini model id)
        if "NOT_FOUND" in message or "is not found" in message.lower():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "AI model not found or not supported. "
                    "Check the recipe_from_image LLM configuration model name "
                    "(Admin → LLM Configuration)."
                ),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse recipe from images",
        ) from e

