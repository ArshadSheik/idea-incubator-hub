"""add user_follows table

Revision ID: c7e88a1b2f00
Revises: fbaf6caf26d6
Create Date: 2026-05-06

"""
from alembic import op
import sqlalchemy as sa


revision = 'c7e88a1b2f00'
down_revision = 'fbaf6caf26d6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_follows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('follower_id', sa.Integer(), nullable=False),
        sa.Column('followed_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['followed_id'], ['users.id']),
        sa.ForeignKeyConstraint(['follower_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('follower_id', 'followed_id', name='uq_user_follow_pair'),
    )
    op.create_index('ix_user_follows_follower_id', 'user_follows', ['follower_id'], unique=False)
    op.create_index('ix_user_follows_followed_id', 'user_follows', ['followed_id'], unique=False)


def downgrade():
    op.drop_index('ix_user_follows_followed_id', table_name='user_follows')
    op.drop_index('ix_user_follows_follower_id', table_name='user_follows')
    op.drop_table('user_follows')
