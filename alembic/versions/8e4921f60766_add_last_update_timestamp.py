"""add last update timestamp

Revision ID: 8e4921f60766
Revises: b3913e0b45ac
Create Date: 2024-04-15 19:10:40.891044

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8e4921f60766'
down_revision = 'b3913e0b45ac'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('schools', sa.Column('update_timestamp', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('schools', 'update_timestamp')
