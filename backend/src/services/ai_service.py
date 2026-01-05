"""
AI Service for LLM interactions using OpenAI API.

This service provides a unified interface for making LLM calls with proper
error handling, rate limiting, and response parsing. Configurations are managed
through LLMConfigService with a fallback hierarchy.
"""

from typing import Optional, Dict, Any, List
from sqlmodel import Session
from openai import AsyncOpenAI, OpenAIError, APIError, RateLimitError, AuthenticationError
from src.services.llm_config_service import LLMConfigService
from src.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)


class AIService:
    """Service for interacting with OpenAI's LLM API with database-driven configuration."""
    
    def __init__(
        self, 
        db: Session,
        llm_config_service: LLMConfigService
    ):
        """
        Initialize the AI service with database configuration support.
        
        Args:
            db: Database session for configuration lookups
            llm_config_service: Service for managing LLM configurations
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required")
        
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            organization=settings.OPENAI_ORG_ID if settings.OPENAI_ORG_ID else None
        )
        self.config_service = llm_config_service
        
        logger.info("AIService initialized with database configuration support")
    
    async def call_llm(
        self,
        user_prompt: str,
        service_name: str = "general",
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make a generic LLM call with configuration fallback and error handling.
        
        Configuration hierarchy (highest to lowest priority):
        1. Runtime parameters (function arguments)
        2. Service-specific configuration (from database)
        3. Global configuration (from database)
        4. Environment variable defaults
        
        Args:
            user_prompt: The user's prompt/question
            service_name: Name of the service for config lookup (e.g., "tag_suggestion")
            system_prompt: Optional system prompt to set context
            model: Model to use (overrides config if provided)
            temperature: Temperature for completion (0.0-2.0, overrides config)
            max_tokens: Maximum tokens to generate (overrides config)
            response_format: 'json' for JSON mode, None for text (overrides config)
            
        Returns:
            Dict containing:
                - content: The LLM response
                - tokens_used: Token usage information
                - model: Model used
                - finish_reason: Completion finish reason
                
        Raises:
            AuthenticationError: Invalid API key
            RateLimitError: Rate limit exceeded
            APIError: General API error
        """
        # Get effective configuration with fallback hierarchy
        override_params = {}
        if model is not None:
            override_params["model"] = model
        if temperature is not None:
            override_params["temperature"] = temperature
        if max_tokens is not None:
            override_params["max_tokens"] = max_tokens
        if response_format is not None:
            override_params["response_format"] = response_format
        if system_prompt is not None:
            override_params["system_prompt"] = system_prompt
        
        config = self.config_service.get_effective_config(
            service_name=service_name,
            override_params=override_params
        )
        
        # Use system prompt from config if not provided directly
        effective_system_prompt = system_prompt or config.get("system_prompt")
        effective_model = config["model"]
        effective_temperature = config["temperature"]
        effective_max_tokens = config["max_tokens"]
        effective_response_format = config.get("response_format")
        
        # Build messages
        messages = []
        if effective_system_prompt:
            messages.append({"role": "system", "content": effective_system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        
        try:
            logger.info(
                f"Calling OpenAI API - service={service_name}, model={effective_model}, "
                f"max_tokens={effective_max_tokens}, temp={effective_temperature}"
            )
            
            # Prepare request parameters
            request_params = {
                "model": effective_model,
                "messages": messages,
                "temperature": effective_temperature,
                "max_tokens": effective_max_tokens
            }
            
            # Add JSON mode if requested
            if effective_response_format == "json":
                request_params["response_format"] = {"type": "json_object"}
                # Ensure system prompt mentions JSON
                if effective_system_prompt and "json" not in effective_system_prompt.lower():
                    messages[0]["content"] += "\n\nProvide your response in valid JSON format."
            
            # Make the API call
            response = await self.client.chat.completions.create(**request_params)
            
            # Extract response
            content = response.choices[0].message.content
            
            # Parse JSON if requested
            if effective_response_format == "json":
                try:
                    content = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    # Return as text if JSON parsing fails
                    pass
            
            result = {
                "content": content,
                "tokens_used": {
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
            
            logger.info(f"LLM call successful. Tokens used: {result['tokens_used']['total']}")
            return result
            
        except AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {str(e)}")
            raise
        except RateLimitError as e:
            logger.warning(f"OpenAI rate limit exceeded: {str(e)}")
            raise
        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {str(e)}")
            raise
    
    async def suggest_tags(
        self, 
        recipe_title: str, 
        ingredients: List[str],
        existing_tags: Optional[List[str]] = None,
        config_override: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Suggest relevant tags for a recipe based on title and ingredients.
        Uses "tag_suggestion" service configuration with fallback hierarchy.
        
        Args:
            recipe_title: The recipe's title
            ingredients: List of ingredient names
            existing_tags: Optional list of tags already applied
            config_override: Optional runtime configuration overrides
            
        Returns:
            List of suggested tag names
        """
        # Get configuration for tag suggestion service
        config = self.config_service.get_effective_config(
            service_name="tag_suggestion",
            override_params=config_override
        )
        
        # Use system prompt from config or fall back to default
        system_prompt = config.get("system_prompt") or """You are a culinary AI assistant. Suggest relevant tags for recipes.
Tags should be concise, accurate, and help users discover recipes.
Categories include: Meal Types, Cuisine Types, Dietary Restrictions, Cooking Methods, Main Ingredients.
Provide your response as a JSON object with a "tags" array containing 3-7 tag suggestions."""
        
        # Build user prompt using template if available
        user_prompt_template = config.get("user_prompt_template")
        if user_prompt_template:
            # Fill in template placeholders
            existing_tags_str = ', '.join(existing_tags) if existing_tags else "None"
            user_prompt = user_prompt_template.replace("{recipe_title}", recipe_title)
            user_prompt = user_prompt.replace("{ingredients}", ', '.join(ingredients))
            user_prompt = user_prompt.replace("{existing_tags}", existing_tags_str)
        else:
            # Fall back to default prompt
            existing_tags_str = f"\nExisting tags: {', '.join(existing_tags)}" if existing_tags else ""
            user_prompt = f"""Recipe: {recipe_title}
Ingredients: {', '.join(ingredients)}{existing_tags_str}

Suggest appropriate tags for this recipe. Consider:
- Type of meal (breakfast, lunch, dinner, dessert)
- Cuisine type (Italian, Mexican, Asian, etc.)
- Dietary restrictions (vegetarian, vegan, gluten-free, etc.)
- Cooking method (baked, fried, grilled, etc.)
- Main ingredients
"""
        
        try:
            response = await self.call_llm(
                user_prompt=user_prompt,
                service_name="tag_suggestion",
                system_prompt=system_prompt,
                **({k: v for k, v in (config_override or {}).items() if k in ['model', 'temperature', 'max_tokens', 'response_format']})
            )
            
            # Extract tags from response
            content = response["content"]
            if isinstance(content, dict) and "tags" in content:
                return content["tags"]
            else:
                logger.warning(f"Unexpected response format for tag suggestions: {content}")
                return []
                
        except Exception as e:
            logger.error(f"Error suggesting tags: {str(e)}")
            return []
    
    async def parse_natural_language_search(
        self, 
        query: str,
        config_override: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convert a natural language query to structured search parameters.
        Uses "natural_language_search" service configuration.
        
        Args:
            query: Natural language search query (e.g., "quick vegetarian dinner under 30 minutes")
            config_override: Optional runtime configuration overrides
            
        Returns:
            Dict with search parameters:
                - keywords: List of search keywords
                - tags: List of relevant tags
                - max_prep_time: Maximum preparation time in minutes
                - max_cook_time: Maximum cooking time in minutes
                - difficulty: Difficulty level (Easy/Medium/Hard)
        """
        try:
            response = await self.call_llm(
                user_prompt=f'Convert this recipe search query to structured parameters:\n"{query}"\n\nConsider time constraints, dietary needs, cooking methods, cuisines, and difficulty levels.',
                service_name="natural_language_search",
                **({k: v for k, v in (config_override or {}).items() if k in ['model', 'temperature', 'max_tokens', 'system_prompt', 'response_format']})
            )
            
            content = response["content"]
            if isinstance(content, dict):
                return content
            else:
                logger.warning(f"Unexpected response format for search parsing: {content}")
                return {}
                
        except Exception as e:
            logger.error(f"Error parsing natural language search: {str(e)}")
            return {}
    
    async def calculate_nutrition(
        self, 
        ingredients: List[Dict[str, str]],
        config_override: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Estimate nutrition facts for a recipe based on ingredients.
        Uses "nutrition_calculation" service configuration.
        
        Args:
            ingredients: List of ingredients with 'name' and 'amount'
            config_override: Optional runtime configuration overrides
            
        Returns:
            Dict with estimated nutrition per serving:
                - calories: estimated calories
                - protein: protein in grams
                - carbs: carbohydrates in grams
                - fat: fat in grams
                - fiber: fiber in grams
        """
        ingredients_str = "\n".join([f"- {ing['name']}: {ing['amount']}" for ing in ingredients])
        user_prompt = f"""Estimate the nutritional content per serving for a recipe with these ingredients:

{ingredients_str}

Provide reasonable estimates based on typical portions."""
        
        try:
            response = await self.call_llm(
                user_prompt=user_prompt,
                service_name="nutrition_calculation",
                **({k: v for k, v in (config_override or {}).items() if k in ['model', 'temperature', 'max_tokens', 'system_prompt', 'response_format']})
            )
            
            content = response["content"]
            if isinstance(content, dict):
                return content
            else:
                logger.warning(f"Unexpected response format for nutrition calculation: {content}")
                return {}
                
        except Exception as e:
            logger.error(f"Error calculating nutrition: {str(e)}")
            return {}

