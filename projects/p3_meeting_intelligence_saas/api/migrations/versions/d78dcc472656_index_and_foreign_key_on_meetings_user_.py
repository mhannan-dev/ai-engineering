"""index and foreign key on meetings.user_id

Revision ID: d78dcc472656
Revises: 1eee3f124151
Create Date: 2026-10-02 23:16:55.516938

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd78dcc472656'
down_revision: str | Sequence[str] | None = '1eee3f124151'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


FK_NAME = 'fk_meetings_user_id_users'


def upgrade() -> None:
    """Upgrade schema."""
    # Orphaned meetings (pointing at deleted users) would block the FK; they are unreachable anyway
    op.execute("DELETE FROM meetings WHERE user_id IS NOT NULL AND user_id NOT IN (SELECT id FROM users)")
    # batch mode: SQLite can't ALTER TABLE ... ADD CONSTRAINT, so it rebuilds the table
    with op.batch_alter_table('meetings') as batch_op:
        batch_op.create_index('ix_meetings_user_id', ['user_id'], unique=False)
        batch_op.create_foreign_key(FK_NAME, 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    # MySQL needs the FK dropped before the index that backs it
    with op.batch_alter_table('meetings') as batch_op:
        batch_op.drop_constraint(FK_NAME, type_='foreignkey')
        batch_op.drop_index('ix_meetings_user_id')
