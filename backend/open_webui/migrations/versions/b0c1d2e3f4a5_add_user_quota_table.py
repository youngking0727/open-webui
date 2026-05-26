"""Add user_quota table

Revision ID: b0c1d2e3f4a5
Revises: a0b1c2d3e4f5
Create Date: 2026-05-25 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from open_webui.migrations.util import get_existing_tables

revision: str = "b0c1d2e3f4a5"
down_revision: Union[str, None] = "a0b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = set(get_existing_tables())

    if "user_quota" not in existing_tables:
        op.create_table(
            "user_quota",
            sa.Column("user_id", sa.String(), nullable=False, primary_key=True),
            sa.Column(
                "request_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
            sa.Column("quota_date", sa.String(), nullable=False),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
        )


def downgrade() -> None:
    op.drop_table("user_quota")