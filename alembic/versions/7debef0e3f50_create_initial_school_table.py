"""create initial school table

Revision ID: 7debef0e3f50
Revises:
Create Date: 2020-02-01 16:18:24.795672

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7debef0e3f50"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "schools",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("address2", sa.String(), nullable=True),
        sa.Column("zip", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("school_type", sa.String(), nullable=True),
        sa.Column("legal_status", sa.String(), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("fax", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("director", sa.String(), nullable=True),
        sa.Column("raw", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("schools")
    # ### end Alembic commands ###
