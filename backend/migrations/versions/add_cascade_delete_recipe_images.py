"""add cascade delete to recipe_images foreign key

Revision ID: cascade_recipe_images
Revises: preserve_lang_prompt
Create Date: 2026-04-16 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = "cascade_recipe_images"
down_revision: Union[str, None] = "preserve_lang_prompt"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("recipe_images_recipe_id_fkey", "recipe_images", type_="foreignkey")
    op.create_foreign_key(
        "recipe_images_recipe_id_fkey",
        "recipe_images",
        "recipes",
        ["recipe_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("recipe_images_recipe_id_fkey", "recipe_images", type_="foreignkey")
    op.create_foreign_key(
        "recipe_images_recipe_id_fkey",
        "recipe_images",
        "recipes",
        ["recipe_id"],
        ["id"],
    )
