"""add recipe_from_image llm config

Revision ID: add_recipe_image_config
Revises: create_recipe_images
Create Date: 2026-04-16 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
from datetime import datetime, timezone
import uuid

revision: str = "add_recipe_image_config"
down_revision: Union[str, None] = "create_recipe_images"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add LLM configuration for recipe_from_image service."""
    config_uuid = str(uuid.uuid4())
    default_admin_uuid = "00000000-0000-0000-0000-000000000000"
    now = datetime.now(timezone.utc)

    op.execute(
        f"""
        INSERT INTO llm_configs (
            uuid, config_type, service_name, provider, model,
            temperature, max_tokens, system_prompt, user_prompt_template,
            response_format, is_active, created_by, created_at, updated_at, description
        ) VALUES (
            '{config_uuid}',
            'SERVICE',
            'recipe_from_image',
            'OPENAI',
            'gpt-4o',
            0.3,
            2000,
            'You are a culinary AI assistant that extracts recipes from images. Analyze the provided image(s) which may contain handwritten or printed recipes, photos of prepared food, or cooking steps. Extract all recipe information and return it as a JSON object with these fields:
- "title": string (recipe name)
- "description": string (brief description)
- "ingredients": array of objects with "name" and "amount" strings
- "instructions": array of step strings
- "preparation_time": integer (minutes, estimate if not stated)
- "cooking_time": integer (minutes, estimate if not stated)
- "servings": integer (estimate if not stated)
- "difficulty_level": string ("Easy", "Medium", or "Hard")
IMPORTANT: Keep the recipe in its original language. Do NOT translate. If the recipe is in Hebrew, return all text fields in Hebrew. If it is in French, return in French, etc. If information is unclear, make reasonable estimates.',
            'Please analyze the attached image(s) and extract the recipe. The recipe language may be {{language_hint}}. Return a complete JSON object with all recipe fields.',
            'json',
            true,
            '{default_admin_uuid}',
            '{now.isoformat()}',
            '{now.isoformat()}',
            'Configuration for AI-powered recipe extraction from images (vision model)'
        )
        """
    )


def downgrade() -> None:
    """Remove recipe_from_image LLM configuration."""
    op.execute(
        """
        DELETE FROM llm_configs
        WHERE service_name = 'recipe_from_image' AND config_type = 'SERVICE';
        """
    )
