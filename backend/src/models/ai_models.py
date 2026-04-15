"""Pydantic models for AI-related API requests and responses."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from src.utils.sanitization import sanitize_text, MAX_LENGTHS


class AITestRequest(BaseModel):
    """Request model for testing LLM calls (admin only)."""
    
    model: str = Field(
        default="gpt-4o-mini",
        max_length=MAX_LENGTHS["llm_model_name"],
        description="OpenAI model to use (e.g., gpt-4o, gpt-4o-mini, gpt-3.5-turbo)"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        max_length=MAX_LENGTHS["ai_prompt"],
        description="System prompt to set AI behavior/context"
    )
    user_prompt: str = Field(
        ...,
        description="User's prompt/question for the AI",
        min_length=1,
        max_length=MAX_LENGTHS["ai_prompt"]
    )
    temperature: Optional[float] = Field(
        default=0.7,
        description="Sampling temperature (0.0-2.0)",
        ge=0.0,
        le=2.0
    )
    max_tokens: Optional[int] = Field(
        default=1000,
        description="Maximum tokens to generate",
        gt=0,
        le=4000
    )
    response_format: Optional[str] = Field(
        default=None,
        description="Response format: 'json' for JSON mode, null for text",
        pattern="^(json)?$"
    )


class AITestResponse(BaseModel):
    """Response model for LLM test calls."""
    
    content: Any = Field(
        ...,
        description="AI-generated response (string or dict if JSON mode)"
    )
    tokens_used: Dict[str, int] = Field(
        ...,
        description="Token usage breakdown"
    )
    model: str = Field(
        ...,
        description="Model used for completion"
    )
    finish_reason: str = Field(
        ...,
        description="Reason completion finished (stop, length, etc.)"
    )
    estimated_cost: float = Field(
        ...,
        description="Estimated cost in USD"
    )


class TagSuggestionRequest(BaseModel):
    """Request model for AI tag suggestions."""
    
    recipe_title: str = Field(..., min_length=1, max_length=MAX_LENGTHS["recipe_title"])
    ingredients: List[str] = Field(..., min_length=1)
    existing_tags: Optional[List[str]] = None

    @field_validator("recipe_title")
    @classmethod
    def sanitize_recipe_title(cls, v: str) -> str:
        return sanitize_text(v, max_length=MAX_LENGTHS["recipe_title"])

    @field_validator("ingredients")
    @classmethod
    def sanitize_ingredients(cls, v: list[str]) -> list[str]:
        return [sanitize_text(i, max_length=MAX_LENGTHS["ingredient_name"]) for i in v]

    @field_validator("existing_tags")
    @classmethod
    def sanitize_existing_tags(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        return [sanitize_text(t, max_length=MAX_LENGTHS["tag_name"]) for t in v]


class TagSuggestionResponse(BaseModel):
    """Response model for AI tag suggestions."""
    
    suggested_tags: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0)


class NaturalLanguageSearchRequest(BaseModel):
    """Request model for natural language recipe search."""
    
    query: str = Field(..., min_length=1, max_length=MAX_LENGTHS["ai_query"])

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        return sanitize_text(v, max_length=MAX_LENGTHS["ai_query"])


class NaturalLanguageSearchResponse(BaseModel):
    """Response model for parsed search parameters."""
    
    keywords: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    max_prep_time: Optional[int] = None
    max_cook_time: Optional[int] = None
    difficulty: Optional[str] = None


class Ingredient(BaseModel):
    """Ingredient model for nutrition calculation."""
    
    name: str = Field(..., max_length=MAX_LENGTHS["ingredient_name"])
    amount: str = Field(..., max_length=MAX_LENGTHS["ingredient_amount"])

    @field_validator("name", "amount")
    @classmethod
    def sanitize_fields(cls, v: str) -> str:
        return sanitize_text(v, max_length=MAX_LENGTHS["ingredient_name"])


class NutritionRequest(BaseModel):
    """Request model for nutrition calculation."""
    
    ingredients: List[Ingredient] = Field(..., min_length=1)
    servings: int = Field(default=1, gt=0, le=100, description="Number of servings the recipe yields; nutrition is per serving")


class NutritionResponse(BaseModel):
    """Response model for nutrition facts."""
    
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None

