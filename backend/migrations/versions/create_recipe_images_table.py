"""create recipe_images table

Revision ID: create_recipe_images
Revises: add_nutrition_config
Create Date: 2026-04-15 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "create_recipe_images"
down_revision: Union[str, None] = "add_nutrition_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recipe_images",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("recipe_id", sa.Integer(), sa.ForeignKey("recipes.id"), nullable=True),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_backend", sa.String(), nullable=False),
        sa.Column("storage_ref", sa.String(), nullable=True),
        sa.Column("data", sa.LargeBinary(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("uuid", name="unique_recipe_image_uuid"),
    )


def downgrade() -> None:
    op.drop_table("recipe_images")
