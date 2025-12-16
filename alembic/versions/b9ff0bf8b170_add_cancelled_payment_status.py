"""add_cancelled_payment_status

Revision ID: b9ff0bf8b170
Revises: 002_update_embedding_dimension
Create Date: 2025-12-16 07:31:17.399817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9ff0bf8b170'
down_revision: Union[str, None] = '002_update_embedding_dimension'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add CANCELLED value to paymentstatus enum
    op.execute("ALTER TYPE paymentstatus ADD VALUE IF NOT EXISTS 'CANCELLED'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # Would need to recreate the enum type to remove a value
    pass
