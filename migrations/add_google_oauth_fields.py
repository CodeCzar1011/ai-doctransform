"""Add Google OAuth fields to User model

Revision ID: add_google_oauth
Revises: 
Create Date: 2025-01-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_google_oauth'
down_revision = None
depends_on = None

def upgrade():
    # Add Google OAuth fields to users table
    op.add_column('users', sa.Column('google_id', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('profile_picture', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('auth_provider', sa.String(20), nullable=False, server_default='local'))
    
    # Make password_hash nullable for Google OAuth users
    op.alter_column('users', 'password_hash', nullable=True)
    
    # Create unique index on google_id
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)

def downgrade():
    # Remove Google OAuth fields
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_column('users', 'auth_provider')
    op.drop_column('users', 'profile_picture')
    op.drop_column('users', 'google_id')
    
    # Make password_hash non-nullable again
    op.alter_column('users', 'password_hash', nullable=False)
