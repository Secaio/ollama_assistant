"""add expiration_date to memory"""

from alembic import op
import sqlalchemy as sa

# IDs de revisão
revision = '20260812_add_expiration_date'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Adiciona coluna expiration_date
    op.add_column('memory', sa.Column('expiration_date', sa.DateTime(), nullable=True))

def downgrade():
    # Remove coluna caso precise reverter
    op.drop_column('memory', 'expiration_date')
