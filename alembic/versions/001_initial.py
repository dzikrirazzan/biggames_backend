"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create enums
    op.execute("CREATE TYPE userrole AS ENUM ('USER', 'ADMIN', 'FINANCE')")
    op.execute("CREATE TYPE roomcategory AS ENUM ('VIP', 'REGULER', 'PS_SERIES', 'SIMULATOR')")
    op.execute("CREATE TYPE roomstatus AS ENUM ('ACTIVE', 'MAINTENANCE', 'INACTIVE')")
    op.execute("CREATE TYPE consoletype AS ENUM ('PS4_SLIM', 'PS4_PRO', 'PS5_SLIM', 'PS5_PRO', 'SWITCH2')")
    op.execute("CREATE TYPE unitstatus AS ENUM ('ACTIVE', 'INACTIVE')")
    op.execute("CREATE TYPE addonpricetype AS ENUM ('FLAT', 'PER_HOUR')")
    op.execute("CREATE TYPE discounttype AS ENUM ('PERCENT', 'FIXED')")
    op.execute("CREATE TYPE reservationstatus AS ENUM ('PENDING_PAYMENT', 'CONFIRMED', 'CANCELLED', 'COMPLETED')")
    op.execute("CREATE TYPE paymentmethod AS ENUM ('QRIS', 'BANK_TRANSFER')")
    op.execute("CREATE TYPE paymentstatus AS ENUM ('WAITING_CONFIRMATION', 'PAID', 'REJECTED')")
    op.execute("CREATE TYPE menucategory AS ENUM ('FOOD', 'DRINK', 'SNACK')")
    op.execute("CREATE TYPE fborderstatus AS ENUM ('PENDING', 'COOKING', 'DELIVERING', 'COMPLETED', 'CANCELLED')")
    op.execute("CREATE TYPE eventtype AS ENUM ('VIEW_ROOM', 'CLICK_ROOM', 'BOOK_ROOM', 'RATE_ROOM')")
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', postgresql.ENUM('USER', 'ADMIN', 'FINANCE', name='userrole', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Rooms table
    op.create_table(
        'rooms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', postgresql.ENUM('VIP', 'REGULER', 'PS_SERIES', 'SIMULATOR', name='roomcategory', create_type=False), nullable=False),
        sa.Column('capacity', sa.Integer, nullable=False),
        sa.Column('base_price_per_hour', sa.Numeric(12, 2), nullable=False),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'MAINTENANCE', 'INACTIVE', name='roomstatus', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Room images table
    op.create_table(
        'room_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
    )
    
    # Units table
    op.create_table(
        'units',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('console_type', postgresql.ENUM('PS4_SLIM', 'PS4_PRO', 'PS5_SLIM', 'PS5_PRO', 'SWITCH2', name='consoletype', create_type=False), nullable=False),
        sa.Column('jumlah_stick', sa.Integer, nullable=False, default=2),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'INACTIVE', name='unitstatus', create_type=False), nullable=False),
    )
    
    # Addons table
    op.create_table(
        'addons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('price_type', postgresql.ENUM('FLAT', 'PER_HOUR', name='addonpricetype', create_type=False), nullable=False),
        sa.Column('price_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
    )
    
    # Promos table
    op.create_table(
        'promos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(50), unique=True, nullable=False),
        sa.Column('discount_type', postgresql.ENUM('PERCENT', 'FIXED', name='discounttype', create_type=False), nullable=False),
        sa.Column('discount_value', sa.Numeric(12, 2), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
    )
    
    # Reservations table
    op.create_table(
        'reservations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_hours', sa.Numeric(5, 2), nullable=False),
        sa.Column('subtotal', sa.Numeric(12, 2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(12, 2), nullable=False, default=0),
        sa.Column('total_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING_PAYMENT', 'CONFIRMED', 'CANCELLED', 'COMPLETED', name='reservationstatus', create_type=False), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Reservation addons table
    op.create_table(
        'reservation_addons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('reservation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reservations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('addon_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('addons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('qty', sa.Integer, nullable=False, default=1),
        sa.Column('price', sa.Numeric(12, 2), nullable=False),
        sa.Column('subtotal', sa.Numeric(12, 2), nullable=False),
    )
    
    # Reviews table
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reservation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reservations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('comment', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('reservation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reservations.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('method', postgresql.ENUM('QRIS', 'BANK_TRANSFER', name='paymentmethod', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('WAITING_CONFIRMATION', 'PAID', 'REJECTED', name='paymentstatus', create_type=False), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('proof_url', sa.String(500), nullable=True),
        sa.Column('reference', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('confirmed_by_admin_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    )
    
    # Menu items table
    op.create_table(
        'menu_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', postgresql.ENUM('FOOD', 'DRINK', 'SNACK', name='menucategory', create_type=False), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('price', sa.Numeric(12, 2), nullable=False),
        sa.Column('stock', sa.Integer, nullable=False, default=0),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('image_url', sa.String(500), nullable=True),
    )
    
    # F&B orders table
    op.create_table(
        'fb_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reservation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reservations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rooms.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'COOKING', 'DELIVERING', 'COMPLETED', 'CANCELLED', name='fborderstatus', create_type=False), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('subtotal', sa.Numeric(12, 2), nullable=False),
        sa.Column('delivery_fee', sa.Numeric(12, 2), nullable=False, default=0),
        sa.Column('total_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # F&B order items table
    op.create_table(
        'fb_order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fb_orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('menu_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('menu_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('qty', sa.Integer, nullable=False),
        sa.Column('price', sa.Numeric(12, 2), nullable=False),
        sa.Column('subtotal', sa.Numeric(12, 2), nullable=False),
    )
    
    # User events table
    op.create_table(
        'user_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', postgresql.ENUM('VIEW_ROOM', 'CLICK_ROOM', 'BOOK_ROOM', 'RATE_ROOM', name='eventtype', create_type=False), nullable=False),
        sa.Column('rating_value', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_user_events_user_id', 'user_events', ['user_id'])
    op.create_index('ix_user_events_room_id', 'user_events', ['room_id'])
    op.create_index('ix_user_events_created_at', 'user_events', ['created_at'])
    
    # Room embeddings table
    op.create_table(
        'room_embeddings',
        sa.Column('room_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rooms.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table('room_embeddings')
    op.drop_table('user_events')
    op.drop_table('fb_order_items')
    op.drop_table('fb_orders')
    op.drop_table('menu_items')
    op.drop_table('payments')
    op.drop_table('reviews')
    op.drop_table('reservation_addons')
    op.drop_table('reservations')
    op.drop_table('promos')
    op.drop_table('addons')
    op.drop_table('units')
    op.drop_table('room_images')
    op.drop_table('rooms')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS eventtype')
    op.execute('DROP TYPE IF EXISTS fborderstatus')
    op.execute('DROP TYPE IF EXISTS menucategory')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS paymentmethod')
    op.execute('DROP TYPE IF EXISTS reservationstatus')
    op.execute('DROP TYPE IF EXISTS discounttype')
    op.execute('DROP TYPE IF EXISTS addonpricetype')
    op.execute('DROP TYPE IF EXISTS unitstatus')
    op.execute('DROP TYPE IF EXISTS consoletype')
    op.execute('DROP TYPE IF EXISTS roomstatus')
    op.execute('DROP TYPE IF EXISTS roomcategory')
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP EXTENSION IF EXISTS vector')
