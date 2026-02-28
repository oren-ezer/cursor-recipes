"""add nutrition llm config

Revision ID: add_nutrition_config
Revises: fix_placeholders_001
Create Date: 2026-01-05 17:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid

# revision identifiers, used by Alembic.
revision: str = 'add_nutrition_config'
down_revision: Union[str, None] = 'fix_placeholders_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add LLM configuration for nutrition_calculation service."""
    nutrition_uuid = str(uuid.uuid4())
    default_admin_uuid = '00000000-0000-0000-0000-000000000000'  # System user
    now = datetime.utcnow()
    
    op.execute(
        f"""
        INSERT INTO llm_configs (
            uuid, config_type, service_name, provider, model, 
            temperature, max_tokens, system_prompt, user_prompt_template,
            response_format, is_active, created_by, created_at, updated_at, description
        ) VALUES (
            '{nutrition_uuid}',
            'SERVICE',
            'nutrition_calculation',
            'OPENAI',
            'gpt-4o-mini',
            0.3,
            800,
            'You are a nutrition expert AI. Provide accurate nutritional estimates for recipe ingredients. Be precise with calculations and consider typical serving sizes.',
            'Estimate the nutritional content per serving for a recipe with these ingredients:

{{ingredients}}

Provide your response in JSON format with the following structure:
{{
  "calories": <number>,
  "protein_g": <number>,
  "carbs_g": <number>,
  "fat_g": <number>,
  "fiber_g": <number>,
  "sodium_mg": <number>
}}

Use reasonable estimates based on typical portions and USDA nutrition data.',
            'json',
            true,
            '{default_admin_uuid}',
            '{now.isoformat()}',
            '{now.isoformat()}',
            'Configuration for recipe nutrition calculation service'
        )
        """
    )


def downgrade() -> None:
    """Remove nutrition_calculation LLM configuration."""
    op.execute(
        """
        DELETE FROM llm_configs 
        WHERE service_name = 'nutrition_calculation' AND config_type = 'SERVICE';
        """
    )

