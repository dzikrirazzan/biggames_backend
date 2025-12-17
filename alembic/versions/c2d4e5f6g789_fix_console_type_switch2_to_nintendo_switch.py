"""fix_console_type_switch2_to_nintendo_switch

Revision ID: c2d4e5f6g789
Revises: a1149a31e607
Create Date: 2025-12-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d4e5f6g789'
down_revision: Union[str, None] = 'a1149a31e607'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update enum type to use NINTENDO_SWITCH instead of SWITCH2
    op.execute("ALTER TYPE consoletype RENAME VALUE 'SWITCH2' TO 'NINTENDO_SWITCH'")


def downgrade() -> None:
    # Revert back to SWITCH2
    op.execute("ALTER TYPE consoletype RENAME VALUE 'NINTENDO_SWITCH' TO 'SWITCH2'")
