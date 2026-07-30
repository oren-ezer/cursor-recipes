"""require recipe_id on recipe_images (no orphans)

Revision ID: require_recipe_id_images
Revises: cascade_recipe_images
Create Date: 2026-07-30 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "require_recipe_id_images"
down_revision: Union[str, None] = "cascade_recipe_images"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove orphan images that are not tied to any recipe
    op.execute("DELETE FROM recipe_images WHERE recipe_id IS NULL")
    op.alter_column(
        "recipe_images",
        "recipe_id",
        existing_type=sa.Integer(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "recipe_images",
        "recipe_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
