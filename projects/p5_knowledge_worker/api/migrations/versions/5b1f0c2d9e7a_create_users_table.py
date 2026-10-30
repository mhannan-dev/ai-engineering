"""create users table

Revision ID: 5b1f0c2d9e7a
Revises: 0ea8e95a4b23
Create Date: 2026-10-29 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5b1f0c2d9e7a'
down_revision: str | Sequence[str] | None = '0ea8e95a4b23'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email', name='uq_users_email')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users')
