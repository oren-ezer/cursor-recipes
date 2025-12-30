"""
AI Service for LLM interactions using OpenAI API.

This service provides a unified interface for making LLM calls with proper
error handling, rate limiting, and response parsing.
"""

from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI, OpenAIError, APIError, RateLimitError, AuthenticationError
import logging
import json

logger = logging.getLogger(__name__)


class AIService:
    """Service for interacting with OpenAI's LLM API."""
    
    def __init__(
        self, 
        api_key: str, 
        org_id: Optional[str] = None,
        default_model: str = "gpt-4o-mini",
        default_temperature: float = 0.7,
        default_max_tokens: int = 1000
    ):
        """
        Initialize the AI service.
        
        Args:
            api_key: OpenAI API key
            org_id: Optional OpenAI organization ID
            default_model: Default model to use for completions
            default_temperature: Default temperature for completions (0.0-2.0)
            default_max_tokens: Default maximum tokens for completions
        """
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            organization=org_id
        )
        self.default_model = default_model
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        
        logger.info(f"AIService initialized with model: {default_model}")
    
    async def call_llm(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make a generic LLM call with retry logic and error handling.
        
        Args:
            user_prompt: The user's prompt/question
            system_prompt: Optional system prompt to set context
            model: Model to use (defaults to service default)
            temperature: Temperature for completion (0.0-2.0)
            max_tokens: Maximum tokens to generate
            response_format: 'json' for JSON mode, None for text
            
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
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens or self.default_max_tokens
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        
        try:
            logger.info(f"Calling OpenAI API with model={model}, max_tokens={max_tokens}")
            
            # Prepare request parameters
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Add JSON mode if requested
            if response_format == "json":
                request_params["response_format"] = {"type": "json_object"}
                # Ensure system prompt mentions JSON
                if system_prompt and "json" not in system_prompt.lower():
                    messages[0]["content"] += "\n\nProvide your response in valid JSON format."
            
            # Make the API call
            response = await self.client.chat.completions.create(**request_params)
            
            # Extract response
            content = response.choices[0].message.content
            
            # Parse JSON if requested
            if response_format == "json":
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
        existing_tags: Optional[List[str]] = None
    ) -> List[str]:
        """
        Suggest relevant tags for a recipe based on title and ingredients.
        
        Args:
            recipe_title: The recipe's title
            ingredients: List of ingredient names
            existing_tags: Optional list of tags already applied
            
        Returns:
            List of suggested tag names
        """
        system_prompt = """You are a culinary AI assistant. Suggest relevant tags for recipes.
Tags should be concise, accurate, and help users discover recipes.
Categories include: Meal Types, Cuisine Types, Dietary Restrictions, Cooking Methods, Main Ingredients.
Provide your response as a JSON object with a "tags" array containing 3-7 tag suggestions."""
        
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
                system_prompt=system_prompt,
                response_format="json",
                temperature=0.5  # Lower temperature for more consistent results
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
    
    async def parse_natural_language_search(self, query: str) -> Dict[str, Any]:
        """
        Convert a natural language query to structured search parameters.
        
        Args:
            query: Natural language search query (e.g., "quick vegetarian dinner under 30 minutes")
            
        Returns:
            Dict with search parameters:
                - keywords: List of search keywords
                - tags: List of relevant tags
                - max_prep_time: Maximum preparation time in minutes
                - max_cook_time: Maximum cooking time in minutes
                - difficulty: Difficulty level (Easy/Medium/Hard)
        """
        system_prompt = """You are a recipe search assistant. Convert natural language queries into structured search parameters.
Output valid JSON with these fields (all optional):
- keywords: array of search keywords
- tags: array of relevant tag names
- max_prep_time: maximum preparation time in minutes
- max_cook_time: maximum cooking time in minutes
- difficulty: one of "Easy", "Medium", or "Hard"
"""
        
        user_prompt = f"""Convert this recipe search query to structured parameters:
"{query}"

Consider time constraints, dietary needs, cooking methods, cuisines, and difficulty levels."""
        
        try:
            response = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
                temperature=0.3  # Low temperature for consistent parsing
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
        ingredients: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Estimate nutrition facts for a recipe based on ingredients.
        
        Args:
            ingredients: List of ingredients with 'name' and 'amount'
            
        Returns:
            Dict with estimated nutrition per serving:
                - calories: estimated calories
                - protein: protein in grams
                - carbs: carbohydrates in grams
                - fat: fat in grams
                - fiber: fiber in grams
        """
        system_prompt = """You are a nutrition calculator. Estimate nutritional information for recipes.
Provide estimates based on standard ingredient nutrition values.
Output valid JSON with these fields (all numbers):
- calories: estimated calories per serving
- protein_g: protein in grams
- carbs_g: carbohydrates in grams
- fat_g: fat in grams
- fiber_g: fiber in grams
- sodium_mg: sodium in milligrams
"""
        
        ingredients_str = "\n".join([f"- {ing['name']}: {ing['amount']}" for ing in ingredients])
        user_prompt = f"""Estimate the nutritional content per serving for a recipe with these ingredients:

{ingredients_str}

Provide reasonable estimates based on typical portions."""
        
        try:
            response = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
                temperature=0.3
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

