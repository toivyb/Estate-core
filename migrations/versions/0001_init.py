"""init schema

Revision ID: 0001_init
Revises: 
Create Date: 2025-08-22 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_table('rent',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_name', sa.String(length=255), nullable=False),
        sa.Column('unit', sa.String(length=64), nullable=True),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('month', sa.String(length=7), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('paid', sa.Boolean(), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('late_fee_cents', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('maintenance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False),
        sa.Column('eta_hours', sa.Integer(), nullable=False),
        sa.Column('triage_note', sa.String(length=512), nullable=True),
        sa.Column('public_token', sa.String(length=48), nullable=True),
        sa.Column('public_enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_token')
    )

def downgrade():
    op.drop_table('maintenance')
    op.drop_table('rent')
    op.drop_table('user')
