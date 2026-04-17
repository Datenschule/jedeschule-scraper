"""add state_key to schools

Revision ID: e6c0d3f4a5b6
Revises: c4a8f1b2d3e4
Create Date: 2026-04-17

Land code (ISO 3166-2:DE without DE- prefix) set by each spider's ``state_key`` and stored on insert/update.
Optional backfill for existing rows: first segment before ``-`` when it is exactly two characters.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision = "e6c0d3f4a5b6"
down_revision = "c4a8f1b2d3e4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("schools", sa.Column("state_key", sa.String(), nullable=True))
    op.execute(
        text(
            "UPDATE schools SET state_key = split_part(id, '-', 1) "
            "WHERE state_key IS NULL "
            "AND strpos(id, '-') > 0 "
            "AND length(split_part(id, '-', 1)) = 2"
        )
    )


def downgrade():
    op.drop_column("schools", "state_key")
