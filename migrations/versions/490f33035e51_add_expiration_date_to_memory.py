"""add expiration_date to memory

Revision ID: 490f33035e51
Revises: bba2851beea3
Create Date: 2026-08-12 10:02:50.416279

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '490f33035e51'
down_revision: Union[str, Sequence[str], None] = 'bba2851beea3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
