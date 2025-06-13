"""create api keys table

Revision ID: 8eaf6006fa28
Revises:
Create Date: 2025-06-06 13:47:00.000000
"""
revision = "8eaf6006fa28"
down_revision = None
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("hashed_key", sa.String(), primary_key=True, nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("refund_address", sa.String(), nullable=True),
        sa.Column("key_expiry_time", sa.Integer(), nullable=True),
        sa.Column("total_spent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_requests", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("api_keys")
