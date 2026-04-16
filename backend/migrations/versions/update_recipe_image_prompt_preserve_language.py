"""update recipe_from_image prompt to preserve original language

Revision ID: preserve_lang_prompt
Revises: add_recipe_image_config
Create Date: 2026-04-16 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = "preserve_lang_prompt"
down_revision: Union[str, None] = "add_recipe_image_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_SYSTEM_PROMPT = (
    "You are a culinary AI assistant that extracts recipes from images. "
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

OLD_SYSTEM_PROMPT = (
    "You are a culinary AI assistant that extracts recipes from images. "
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
    "If the recipe is in a non-English language, translate it to English. "
    "If information is unclear, make reasonable estimates."
)


def upgrade() -> None:
    escaped = NEW_SYSTEM_PROMPT.replace("'", "''")
    op.execute(
        f"""
        UPDATE llm_configs
        SET system_prompt = '{escaped}'
        WHERE service_name = 'recipe_from_image' AND config_type = 'SERVICE';
        """
    )


def downgrade() -> None:
    escaped = OLD_SYSTEM_PROMPT.replace("'", "''")
    op.execute(
        f"""
        UPDATE llm_configs
        SET system_prompt = '{escaped}'
        WHERE service_name = 'recipe_from_image' AND config_type = 'SERVICE';
        """
    )
