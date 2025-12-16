"""fix_room_category_reguler_to_regular

Revision ID: 848ef9c4aeb1
Revises: b9ff0bf8b170
Create Date: 2025-12-16 07:52:23.153185

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '848ef9c4aeb1'
down_revision: Union[str, None] = 'b9ff0bf8b170'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update enum type to use REGULAR instead of REGULER
    op.execute("ALTER TYPE roomcategory RENAME VALUE 'REGULER' TO 'REGULAR'")


def downgrade() -> None:
    # Revert back to REGULER
    op.execute("ALTER TYPE roomcategory RENAME VALUE 'REGULAR' TO 'REGULER'")
