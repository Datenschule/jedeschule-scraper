"""add location to school

Revision ID: b3913e0b45ac
Revises: 7debef0e3f50
Create Date: 2021-02-14 09:09:07.672138

"""
import geoalchemy2

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3913e0b45ac'
down_revision = '7debef0e3f50'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    op.add_column('schools', sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', from_text='ST_GeomFromEWKT', name='geometry'), nullable=True))


def downgrade():
    op.drop_column('schools', 'location')
    conn = op.get_bind()
    conn.execute("DROP EXTENSION IF EXISTS postgis;")
