"""Create llm_configs table

Revision ID: a1b2c3d4e5f6
Revises: f2ed96f7b631
Create Date: 2025-01-04 15:00:00.000000

"""
from typing import Sequence, Union
from datetime import datetime
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f2ed96f7b631'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create llm_configs table
    op.create_table(
        'llm_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(), nullable=False),
        sa.Column('config_type', sa.String(), nullable=False),
        sa.Column('service_name', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False),
        sa.Column('max_tokens', sa.Integer(), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('user_prompt_template', sa.Text(), nullable=True),
        sa.Column('response_format', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_llm_configs_uuid'), 'llm_configs', ['uuid'], unique=True)
    op.create_index(op.f('ix_llm_configs_service_name'), 'llm_configs', ['service_name'], unique=False)
    op.create_index(op.f('ix_llm_configs_created_by'), 'llm_configs', ['created_by'], unique=False)
    
    # Insert default global configuration
    # This will serve as the system-wide default if no service-specific config exists
    default_uuid = str(uuid.uuid4())
    default_admin_uuid = '00000000-0000-0000-0000-000000000000'  # System user
    now = datetime.utcnow()
    
    op.execute(
        f"""
        INSERT INTO llm_configs (
            uuid, config_type, service_name, provider, model, 
            temperature, max_tokens, system_prompt, user_prompt_template,
            response_format, is_active, created_by, created_at, updated_at, description
        ) VALUES (
            '{default_uuid}',
            'GLOBAL',
            NULL,
            'OPENAI',
            'gpt-4o-mini',
            0.7,
            1000,
            'You are a helpful culinary AI assistant specialized in recipes, cooking techniques, and nutrition.',
            NULL,
            'text',
            true,
            '{default_admin_uuid}',
            '{now.isoformat()}',
            '{now.isoformat()}',
            'Default global LLM configuration'
        )
        """
    )
    
    # Insert default configuration for tag suggestion service
    tag_uuid = str(uuid.uuid4())
    op.execute(
        f"""
        INSERT INTO llm_configs (
            uuid, config_type, service_name, provider, model, 
            temperature, max_tokens, system_prompt, user_prompt_template,
            response_format, is_active, created_by, created_at, updated_at, description
        ) VALUES (
            '{tag_uuid}',
            'SERVICE',
            'tag_suggestion',
            'OPENAI',
            'gpt-4o-mini',
            0.5,
            500,
            'You are an AI specialized in categorizing recipes. Suggest relevant tags based on the recipe information provided.',
            'Recipe: {{recipe_title}}\nIngredients: {{ingredients}}\nExisting tags: {{existing_tags}}\n\nSuggest 3-5 relevant tags for this recipe in JSON format.',
            'json',
            true,
            '{default_admin_uuid}',
            '{now.isoformat()}',
            '{now.isoformat()}',
            'Configuration for recipe tag suggestion service'
        )
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_llm_configs_created_by'), table_name='llm_configs')
    op.drop_index(op.f('ix_llm_configs_service_name'), table_name='llm_configs')
    op.drop_index(op.f('ix_llm_configs_uuid'), table_name='llm_configs')
    op.drop_table('llm_configs')

