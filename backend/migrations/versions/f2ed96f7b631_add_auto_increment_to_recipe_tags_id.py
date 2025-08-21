"""add_auto_increment_to_recipe_tags_id

Revision ID: f2ed96f7b631
Revises: b0b11946c06a
Create Date: 2025-08-21 12:42:26.269567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2ed96f7b631'
down_revision: Union[str, None] = 'b0b11946c06a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create a sequence for recipe_tags.id
    op.execute("CREATE SEQUENCE IF NOT EXISTS recipe_tags_id_seq")
    
    # Set the sequence as the default for the id column
    op.execute("ALTER TABLE recipe_tags ALTER COLUMN id SET DEFAULT nextval('recipe_tags_id_seq')")
    
    # Set the sequence to start from the current maximum id value
    op.execute("SELECT setval('recipe_tags_id_seq', COALESCE((SELECT MAX(id) FROM recipe_tags), 0) + 1)")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the default from the id column
    op.execute("ALTER TABLE recipe_tags ALTER COLUMN id DROP DEFAULT")
    
    # Drop the sequence
    op.execute("DROP SEQUENCE IF EXISTS recipe_tags_id_seq")
