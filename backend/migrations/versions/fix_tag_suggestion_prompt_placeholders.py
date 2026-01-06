"""fix tag suggestion prompt placeholders

Revision ID: fix_placeholders_001
Revises: ffdbe03389e8
Create Date: 2026-01-05 17:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fix_placeholders_001'
down_revision: Union[str, None] = 'ffdbe03389e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix the user_prompt_template placeholders from double to single braces."""
    # Update the tag_suggestion service configuration
    # Change {{placeholder}} to {placeholder}
    op.execute(
        """
        UPDATE llm_configs 
        SET user_prompt_template = 'Recipe: {recipe_title}
Ingredients: {ingredients}
Existing tags: {existing_tags}

Suggest 3-5 relevant tags for this recipe in JSON format with a "tags" array.'
        WHERE service_name = 'tag_suggestion' AND config_type = 'SERVICE';
        """
    )


def downgrade() -> None:
    """Revert the placeholder format back to double braces."""
    op.execute(
        """
        UPDATE llm_configs 
        SET user_prompt_template = 'Recipe: {{recipe_title}}
Ingredients: {{ingredients}}
Existing tags: {{existing_tags}}

Suggest 3-5 relevant tags for this recipe in JSON format.'
        WHERE service_name = 'tag_suggestion' AND config_type = 'SERVICE';
        """
    )

