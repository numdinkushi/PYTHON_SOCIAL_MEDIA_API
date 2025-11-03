"""Create posts table

Revision ID: aa852b315121
Revises: 
Create Date: 2025-11-03 13:16:53.327121

"""
# pylint: disable=no-member
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa852b315121'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table first (posts and votes depend on it)
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create posts table (votes depend on it)
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('published', sa.Boolean(),
                  server_default='TRUE', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create votes table (depends on both users and posts)
    op.create_table(
        'votes',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'post_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('votes')
    op.drop_table('posts')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
