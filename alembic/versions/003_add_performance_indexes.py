"""Add performance indexes

Revision ID: 003_add_indexes
Revises: c2d4e5f6g789
Create Date: 2025-12-17 15:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_indexes'
down_revision = 'c2d4e5f6g789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add indexes for frequently queried columns."""
    # Reservations - filter by status and date
    op.create_index('ix_reservations_status', 'reservations', ['status'])
    op.create_index('ix_reservations_start_time', 'reservations', ['start_time'])
    op.create_index('ix_reservations_user_id', 'reservations', ['user_id'])
    op.create_index('ix_reservations_room_id', 'reservations', ['room_id'])
    
    # Payments - filter by status
    op.create_index('ix_payments_status', 'payments', ['status'])
    op.create_index('ix_payments_reservation_id', 'payments', ['reservation_id'])
    
    # FB Orders - filter by status
    op.create_index('ix_fb_orders_status', 'fb_orders', ['status'])
    op.create_index('ix_fb_orders_user_id', 'fb_orders', ['user_id'])
    
    # Rooms - filter by status and category
    op.create_index('ix_rooms_status', 'rooms', ['status'])
    op.create_index('ix_rooms_category', 'rooms', ['category'])
    
    # Menu items - filter by category and active status
    op.create_index('ix_menu_items_category', 'menu_items', ['category'])
    op.create_index('ix_menu_items_is_active', 'menu_items', ['is_active'])


def downgrade() -> None:
    """Remove indexes."""
    op.drop_index('ix_reservations_status', 'reservations')
    op.drop_index('ix_reservations_start_time', 'reservations')
    op.drop_index('ix_reservations_user_id', 'reservations')
    op.drop_index('ix_reservations_room_id', 'reservations')
    
    op.drop_index('ix_payments_status', 'payments')
    op.drop_index('ix_payments_reservation_id', 'payments')
    
    op.drop_index('ix_fb_orders_status', 'fb_orders')
    op.drop_index('ix_fb_orders_user_id', 'fb_orders')
    
    op.drop_index('ix_rooms_status', 'rooms')
    op.drop_index('ix_rooms_category', 'rooms')
    
    op.drop_index('ix_menu_items_category', 'menu_items')
    op.drop_index('ix_menu_items_is_active', 'menu_items')
