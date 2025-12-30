"""Pydantic models for AI-related API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class AITestRequest(BaseModel):
    """Request model for testing LLM calls."""
    
    model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use (e.g., gpt-4o, gpt-4o-mini, gpt-3.5-turbo)"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt to set AI behavior/context"
    )
    user_prompt: str = Field(
        ...,
        description="User's prompt/question for the AI",
        min_length=1
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
    
    recipe_title: str = Field(..., min_length=1)
    ingredients: List[str] = Field(..., min_length=1)
    existing_tags: Optional[List[str]] = None


class TagSuggestionResponse(BaseModel):
    """Response model for AI tag suggestions."""
    
    suggested_tags: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0)


class NaturalLanguageSearchRequest(BaseModel):
    """Request model for natural language recipe search."""
    
    query: str = Field(..., min_length=1, max_length=500)


class NaturalLanguageSearchResponse(BaseModel):
    """Response model for parsed search parameters."""
    
    keywords: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    max_prep_time: Optional[int] = None
    max_cook_time: Optional[int] = None
    difficulty: Optional[str] = None


class Ingredient(BaseModel):
    """Ingredient model for nutrition calculation."""
    
    name: str
    amount: str


class NutritionRequest(BaseModel):
    """Request model for nutrition calculation."""
    
    ingredients: List[Ingredient] = Field(..., min_length=1)


class NutritionResponse(BaseModel):
    """Response model for nutrition facts."""
    
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None

