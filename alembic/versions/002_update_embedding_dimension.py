"""Update embedding dimension for HuggingFace

Revision ID: 002_update_embedding_dimension
Revises: 001_initial
Create Date: 2025-12-15

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '002_update_embedding_dimension'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade to 384-dimensional embeddings for HuggingFace."""
    # First, truncate the table to remove existing data
    # (embeddings need to be regenerated anyway due to dimension change)
    op.execute('TRUNCATE TABLE room_embeddings')
    
    # Drop the existing embedding column
    op.drop_column('room_embeddings', 'embedding')
    
    # Add the new embedding column with 384 dimensions (no default, nullable first)
    op.add_column(
        'room_embeddings',
        sa.Column('embedding', Vector(384), nullable=True)
    )
    
    # Make it not nullable after adding
    op.alter_column('room_embeddings', 'embedding', nullable=False)


def downgrade() -> None:
    """Downgrade back to 1536-dimensional embeddings."""
    # Truncate first
    op.execute('TRUNCATE TABLE room_embeddings')
    
    # Drop the 384-dim column
    op.drop_column('room_embeddings', 'embedding')
    
    # Add back the 1536-dim column
    op.add_column(
        'room_embeddings',
        sa.Column('embedding', Vector(1536), nullable=True)
    )
    
    # Make it not nullable
    op.alter_column('room_embeddings', 'embedding', nullable=False)
