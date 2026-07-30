"""
AI Service for LLM interactions across multiple providers.

This service provides a unified interface for making LLM calls with proper
error handling, rate limiting, and response parsing. Configurations are managed
through LLMConfigService with a fallback hierarchy. Provider SDKs are selected
from the effective config's ``provider`` field.
"""

from typing import Optional, Dict, Any, List
from sqlmodel import Session
from openai import AuthenticationError, RateLimitError, APIError
from src.services.llm_config_service import LLMConfigService
from src.services.llm_providers import LLMProviderBackend, create_provider_backends
from src.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)


def _parse_json_content(content: str) -> Any:
    """Parse JSON from an LLM string, tolerating markdown code fences."""
    text = content.strip()
    if not text:
        raise json.JSONDecodeError("Empty content", content, 0)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip ```json ... ``` or ``` ... ``` wrappers Gemini often returns
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop opening fence (``` or ```json)
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # Drop closing fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        return json.loads(text)

    # Fallback: extract outermost {...} or [...]
    start_obj, end_obj = text.find("{"), text.rfind("}")
    start_arr, end_arr = text.find("["), text.rfind("]")
    if start_obj != -1 and end_obj > start_obj and (start_arr == -1 or start_obj < start_arr):
        return json.loads(text[start_obj : end_obj + 1])
    if start_arr != -1 and end_arr > start_arr:
        return json.loads(text[start_arr : end_arr + 1])

    raise json.JSONDecodeError("No JSON object found", content, 0)


class AIService:
    """Service for interacting with LLMs using database-driven multi-provider config."""

    def __init__(
        self,
        db: Session,
        llm_config_service: LLMConfigService,
    ):
        """
        Initialize the AI service with available provider backends.

        Args:
            db: Database session for configuration lookups
            llm_config_service: Service for managing LLM configurations
        """
        self.config_service = llm_config_service
        self._backends = create_provider_backends(settings)
        if not self._backends:
            raise ValueError(
                "At least one LLM API key is required "
                "(OPENAI_API_KEY, GOOGLE_API_KEY, or ANTHROPIC_API_KEY)"
            )

        # Back-compat for code/tests that still reference service.client (OpenAI)
        openai_backend = self._backends.get("OPENAI")
        self.client = getattr(openai_backend, "client", None)

        logger.info(
            "AIService initialized with providers: %s",
            ", ".join(sorted(self._backends.keys())),
        )

    def _get_backend(self, provider: str) -> LLMProviderBackend:
        key = (provider or "OPENAI").upper()
        backend = self._backends.get(key)
        if not backend:
            available = ", ".join(sorted(self._backends.keys())) or "none"
            raise ValueError(
                f"LLM provider '{key}' is not configured. Available: {available}"
            )
        return backend

    async def call_llm(
        self,
        user_prompt: str,
        service_name: str = "general",
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None,
        image_urls: Optional[List[str]] = None,
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
            image_urls: Optional list of image URLs (base64 data URIs or http URLs)
                        for vision models. Sent as image_url content parts.

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
            override_params=override_params,
        )

        effective_system_prompt = system_prompt or config.get("system_prompt")
        effective_model = config["model"]
        effective_temperature = config["temperature"]
        effective_max_tokens = config["max_tokens"]
        effective_response_format = config.get("response_format")
        effective_provider = (config.get("provider") or "OPENAI").upper()

        messages: List[Dict[str, Any]] = []
        if effective_system_prompt:
            messages.append({"role": "system", "content": effective_system_prompt})

        if image_urls:
            user_content: List[Dict[str, Any]] = [{"type": "text", "text": user_prompt}]
            for url in image_urls:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": url, "detail": "high"},
                })
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": user_prompt})

        response_format_param = None
        if effective_response_format == "json":
            response_format_param = {"type": "json_object"}
            if effective_system_prompt and "json" not in effective_system_prompt.lower():
                messages[0]["content"] += "\n\nProvide your response in valid JSON format."

        try:
            backend = self._get_backend(effective_provider)
            logger.info(
                "Calling LLM - provider=%s service=%s model=%s max_tokens=%s temp=%s",
                effective_provider,
                service_name,
                effective_model,
                effective_max_tokens,
                effective_temperature,
            )

            result = await backend.call(
                messages=messages,
                model=effective_model,
                temperature=effective_temperature,
                max_tokens=effective_max_tokens,
                response_format=response_format_param,
            )

            content = result["content"]
            if effective_response_format == "json" and isinstance(content, str):
                try:
                    content = _parse_json_content(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")

            result = {**result, "content": content}

            logger.info(
                "LLM call successful. Tokens used: %s",
                result["tokens_used"].get("total"),
            )
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
            logger.error(f"Unexpected error calling LLM: {str(e)}")
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
        servings: int = 1,
        config_override: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Estimate nutrition facts for a recipe based on ingredients.
        Uses "nutrition_calculation" service configuration.
        
        Args:
            ingredients: List of ingredients with 'name' and 'amount'
            servings: Number of servings the recipe yields; returned values are per serving
            config_override: Optional runtime configuration overrides
            
        Returns:
            Dict with estimated nutrition per serving:
                - calories: estimated calories per serving
                - protein_g: protein in grams per serving
                - carbs_g: carbohydrates in grams per serving
                - fat_g: fat in grams per serving
                - fiber_g: fiber in grams per serving
                - sodium_mg: sodium in milligrams per serving
        """
        # Get configuration for nutrition service
        config = self.config_service.get_effective_config(
            service_name="nutrition_calculation",
            override_params=config_override
        )
        
        # Format ingredients
        ingredients_str = "\n".join([f"- {ing['name']}: {ing['amount']}" for ing in ingredients])
        
        # Use system prompt from config or fall back to default
        system_prompt = config.get("system_prompt") or """You are a nutrition expert AI. 
Provide accurate nutritional estimates for recipe ingredients based on USDA data and typical serving sizes.
Return your response in JSON format with numeric values."""
        
        # Build user prompt using template if available
        user_prompt_template = config.get("user_prompt_template")
        if user_prompt_template:
            # Replace placeholders in template
            user_prompt = user_prompt_template.replace("{ingredients}", ingredients_str)
            user_prompt = user_prompt.replace("{servings}", str(servings))
        else:
            # Fall back to default prompt
            user_prompt = f"""Estimate the nutritional content PER SERVING for a recipe that yields {servings} serving(s).

Ingredients (total for full recipe):
{ingredients_str}

Divide total nutrition by {servings} to get per-serving values.
Provide reasonable estimates based on typical portions and USDA nutrition data.
Return as JSON with: calories, protein_g, carbs_g, fat_g, fiber_g, sodium_mg (all per serving)"""
        
        try:
            response = await self.call_llm(
                user_prompt=user_prompt,
                service_name="nutrition_calculation",
                system_prompt=system_prompt,
                **({k: v for k, v in (config_override or {}).items() if k in ['model', 'temperature', 'max_tokens', 'response_format']})
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

    async def parse_recipe_from_images(
        self,
        image_data_uris: List[str],
        language_hint: Optional[str] = None,
        config_override: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Extract a recipe from one or more images using a vision-capable model.

        The images can contain handwritten or printed recipes, photos of food,
        preparation steps, etc. The LLM uses OCR + understanding to produce
        structured recipe data.

        Args:
            image_data_uris: List of base64 data URIs (data:image/...;base64,...)
            language_hint: Optional hint about the language (e.g. "Hebrew", "English")
            config_override: Optional runtime configuration overrides

        Returns:
            Dict with recipe fields: title, description, ingredients, instructions,
            preparation_time, cooking_time, servings, difficulty_level
        """
        config = self.config_service.get_effective_config(
            service_name="recipe_from_image",
            override_params=config_override,
        )

        system_prompt = config.get("system_prompt") or (
            "You are a culinary AI that extracts recipes from images. "
            "Analyze the provided image(s) which may contain handwritten or printed recipes, "
            "photos of prepared food, or cooking steps. "
            "Extract all recipe information and return it as a JSON object with these fields:\n"
            '- "title": string (recipe name)\n'
            '- "description": string (brief description)\n'
            '- "ingredients": array of objects with "name" and "amount" strings\n'
            '- "instructions": array of step strings\n'
            '- "preparation_time": integer (minutes, estimate if not stated)\n'
            '- "cooking_time": integer (minutes, estimate if not stated)\n'
            '- "servings": integer (estimate if not stated)\n'
            '- "difficulty_level": string ("Easy", "Medium", or "Hard")\n'
            "IMPORTANT: Keep the recipe in its original language. Do NOT translate. "
            "If the recipe is in Hebrew, return all text fields in Hebrew. "
            "If it is in French, return in French, etc. "
            "If information is unclear, make reasonable estimates."
        )

        user_prompt_template = config.get("user_prompt_template")
        if user_prompt_template:
            lang = language_hint or "auto-detect"
            user_prompt = user_prompt_template.replace("{language_hint}", lang)
        else:
            lang_note = f" The recipe may be in {language_hint}." if language_hint else ""
            user_prompt = (
                f"Please analyze the attached image(s) and extract the recipe.{lang_note} "
                "Return a complete JSON object with all recipe fields."
            )

        try:
            response = await self.call_llm(
                user_prompt=user_prompt,
                service_name="recipe_from_image",
                system_prompt=system_prompt,
                image_urls=image_data_uris,
                response_format="json",
                **({
                    k: v
                    for k, v in (config_override or {}).items()
                    if k in ["model", "temperature", "max_tokens"]
                }),
            )

            content = response["content"]
            if isinstance(content, dict):
                return content
            logger.warning(f"Unexpected response format for recipe parsing: {content}")
            return {}

        except Exception as e:
            logger.error(f"Error parsing recipe from images: {str(e)}")
            raise

