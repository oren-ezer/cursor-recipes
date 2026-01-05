"""update_llm_config_enum_values_to_uppercase

Revision ID: ffdbe03389e8
Revises: a1b2c3d4e5f6
Create Date: 2026-01-05 08:35:46.389302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffdbe03389e8'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Update existing LLM config records to use uppercase enum values.
    This is a data migration to fix enum values from lowercase to uppercase.
    """
    # Update config_type values
    op.execute("""
        UPDATE llm_configs 
        SET config_type = UPPER(config_type)
        WHERE config_type IN ('global', 'service')
    """)
    
    # Update provider values
    op.execute("""
        UPDATE llm_configs 
        SET provider = UPPER(provider)
        WHERE provider IN ('openai', 'anthropic', 'google')
    """)


def downgrade() -> None:
    """
    Revert enum values back to lowercase.
    """
    # Revert config_type values
    op.execute("""
        UPDATE llm_configs 
        SET config_type = LOWER(config_type)
        WHERE config_type IN ('GLOBAL', 'SERVICE')
    """)
    
    # Revert provider values
    op.execute("""
        UPDATE llm_configs 
        SET provider = LOWER(provider)
        WHERE provider IN ('OPENAI', 'ANTHROPIC', 'GOOGLE')
    """)
