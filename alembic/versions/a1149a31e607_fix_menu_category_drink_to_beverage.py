"""fix_menu_category_drink_to_beverage

Revision ID: a1149a31e607
Revises: 848ef9c4aeb1
Create Date: 2025-12-16 07:54:21.066039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1149a31e607'
down_revision: Union[str, None] = '848ef9c4aeb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update enum type to use BEVERAGE instead of DRINK
    op.execute("ALTER TYPE menucategory RENAME VALUE 'DRINK' TO 'BEVERAGE'")


def downgrade() -> None:
    # Revert back to DRINK
    op.execute("ALTER TYPE menucategory RENAME VALUE 'BEVERAGE' TO 'DRINK'")
