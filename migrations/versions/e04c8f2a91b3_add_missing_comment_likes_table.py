"""add missing comment_likes table

Revision ID: e04c8f2a91b3
Revises: 7ba6e18ee70b
Create Date: 2026-05-17

The 1d49cbf24a6a revision was mis-generated: it only created task_activities.
"""
from alembic import op
import sqlalchemy as sa


revision = 'e04c8f2a91b3'
down_revision = '7ba6e18ee70b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'comment_likes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('comment_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'comment_id', name='uq_comment_like'),
    )
    with op.batch_alter_table('comment_likes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_comment_likes_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_comment_likes_comment_id'), ['comment_id'], unique=False)


def downgrade():
    with op.batch_alter_table('comment_likes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_comment_likes_comment_id'))
        batch_op.drop_index(batch_op.f('ix_comment_likes_user_id'))

    op.drop_table('comment_likes')
