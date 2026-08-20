"""update recipe_from_image prompt for multi-recipe extraction

Revision ID: multi_recipe_prompt
Revises: 9e9e75714db1
Create Date: 2026-08-19 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = "multi_recipe_prompt"
down_revision: Union[str, None] = "9e9e75714db1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_SYSTEM_PROMPT = (
    "You are an expert OCR assistant specializing in reading handwritten and printed "
    "recipes from images, both in Hebrew and in English.\n\n"
    "## Critical instruction\n"
    "You MUST faithfully transcribe text that is ACTUALLY VISIBLE in the image. "
    "Do NOT generate, invent, guess, or hallucinate any recipe content. "
    "If you cannot read the image or it does not contain a recipe, return empty fields.\n\n"
    "## Process \u2014 follow these steps in order:\n"
    "1. FIRST, read the image and identify every line of visible text. "
    "Note the script/language (Hebrew, English, etc.).\n"
    "2. SECOND, transcribe each line of text exactly as written, character by character. "
    "For Hebrew handwriting, pay close attention to easily confused letters: "
    "\u05d1/\u05db, \u05d2/\u05e0, \u05d3/\u05e8, \u05d4/\u05d7, \u05d5/\u05d6, "
    "\u05db/\u05da, \u05de/\u05dd, \u05e0/\u05df, \u05e4/\u05e3, \u05e6/\u05e5.\n"
    "3. THIRD, organize the transcribed text into the JSON structure below.\n\n"
    "## Strict rules\n"
    "- NEVER translate. Output in the SAME language as the source text.\n"
    "- NEVER add ingredients, steps, or details not visible in the image.\n"
    '- If a word is illegible, write "[unclear]" \u2014 do NOT guess.\n'
    "- Only estimate numeric fields (preparation_time, cooking_time, servings) "
    "when they are NOT written in the image.\n"
    "- If the image does not contain a recipe, return "
    '{"recipes": [{"title": "", "description": "No recipe found in image", '
    '"ingredients": [], "instructions": [], "preparation_time": 0, '
    '"cooking_time": 0, "servings": 0, "difficulty_level": "Easy"}]}.\n\n'
    "## Multiple recipes\n"
    "If the image contains multiple distinct recipes, return ALL of them as separate "
    'objects inside the "recipes" JSON array. If there is only one recipe, still wrap '
    "it in the array.\n\n"
    "## JSON output format\n"
    'Always wrap your response in a top-level object with a "recipes" array:\n'
    "{\n"
    '  "recipes": [\n'
    "    {\n"
    '      "title": "recipe name as written",\n'
    '      "description": "brief description in the same language",\n'
    '      "ingredients": [{"name": "as written", "amount": "as written"}],\n'
    '      "instructions": ["step as written", ...],\n'
    '      "preparation_time": integer minutes,\n'
    '      "cooking_time": integer minutes,\n'
    '      "servings": integer,\n'
    '      "difficulty_level": "Easy" or "Medium" or "Hard"\n'
    "    }\n"
    "  ]\n"
    "}"
)

NEW_USER_PROMPT = (
    "Read the handwritten/printed recipe(s) in the attached image(s) carefully "
    "word by word.\n"
    "The recipe language is {language_hint}.\n"
    "Return ALL text fields in {language_hint} \u2014 do NOT translate to any other language.\n"
    "Transcribe ONLY what you can see. Do NOT add any ingredients or steps that are "
    "not visible in the image.\n"
    "If the image contains multiple distinct recipes, return ALL of them.\n"
    'Return a JSON object with a "recipes" array containing each recipe.'
)

OLD_USER_PROMPT = (
    "Read the handwritten/printed recipe in the attached image(s) carefully "
    "word by word.\n"
    "The recipe language is {language_hint}.\n"
    "Return ALL text fields in {language_hint} \u2014 do NOT translate to any other language.\n"
    "Transcribe ONLY what you can see. Do NOT add any ingredients or steps that are "
    "not visible in the image.\n"
    "Return a JSON object."
)


def upgrade() -> None:
    """Update recipe_from_image LLM config to support multi-recipe extraction."""
    escaped_sys = NEW_SYSTEM_PROMPT.replace("'", "''")
    escaped_usr = NEW_USER_PROMPT.replace("'", "''")
    op.execute(
        f"""
        UPDATE llm_configs
        SET system_prompt = '{escaped_sys}',
            user_prompt_template = '{escaped_usr}',
            updated_at = now()
        WHERE service_name = 'recipe_from_image'
          AND config_type = 'SERVICE'
          AND is_active = true;
        """
    )


def downgrade() -> None:
    """Revert to single-recipe prompt (user_prompt only; system_prompt not reverted)."""
    escaped_usr = OLD_USER_PROMPT.replace("'", "''")
    op.execute(
        f"""
        UPDATE llm_configs
        SET user_prompt_template = '{escaped_usr}',
            updated_at = now()
        WHERE service_name = 'recipe_from_image'
          AND config_type = 'SERVICE'
          AND is_active = true;
        """
    )
