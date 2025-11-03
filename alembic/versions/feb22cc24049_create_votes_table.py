"""create_votes_table

Revision ID: feb22cc24049
Revises: 64dc2de37bd0
Create Date: 2025-11-03 14:45:31.075247

"""
# pylint: disable=no-member
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'feb22cc24049'
down_revision: Union[str, Sequence[str], None] = '64dc2de37bd0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create votes table."""
    op.create_table(
        'votes',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'post_id')
    )


def downgrade() -> None:
    """Drop votes table."""
    op.drop_table('votes')
