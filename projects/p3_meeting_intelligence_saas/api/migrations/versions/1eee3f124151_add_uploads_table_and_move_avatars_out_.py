"""add uploads table and move avatars out of users

Revision ID: 1eee3f124151
Revises: e503ae206df9
Create Date: 2026-10-02 23:02:58.852717

"""
import mimetypes
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

from meeting_intelligence.config import get_settings

# revision identifiers, used by Alembic.
revision: str = '1eee3f124151'
down_revision: str | Sequence[str] | None = 'e503ae206df9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

URL_PREFIX = "/uploads/"
# mimetypes misses some of these on Windows (e.g. .webp)
IMAGE_TYPES = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif"}


def _guess_content_type(filename: str) -> str:
    ext = filename[filename.rfind("."):].lower() if "." in filename else ""
    return IMAGE_TYPES.get(ext) or mimetypes.guess_type(filename)[0] or "application/octet-stream"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('uploads',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('category', sa.String(length=32), nullable=False),
    sa.Column('original_filename', sa.String(length=255), nullable=True),
    sa.Column('stored_path', sa.String(length=512), nullable=False),
    sa.Column('content_type', sa.String(length=127), nullable=False),
    sa.Column('size_bytes', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('stored_path')
    )
    op.create_index('ix_uploads_user_id_category', 'uploads', ['user_id', 'category'], unique=False)

    # Data: move existing users.avatar values into uploads rows before dropping the column
    conn = op.get_bind()
    upload_dir = get_settings().UPLOAD_DIR
    uploads = sa.table(
        'uploads',
        sa.column('id', sa.String), sa.column('user_id', sa.String), sa.column('category', sa.String),
        sa.column('original_filename', sa.String), sa.column('stored_path', sa.String),
        sa.column('content_type', sa.String), sa.column('size_bytes', sa.BigInteger),
        sa.column('created_at', sa.DateTime),
    )
    rows = conn.execute(sa.text("SELECT id, avatar FROM users WHERE avatar IS NOT NULL")).fetchall()
    for user_id, avatar in rows:
        if not avatar.startswith(URL_PREFIX):
            continue  # external URL / unknown format: not a file we manage
        stored_path = avatar[len(URL_PREFIX):]
        file = upload_dir / stored_path
        if not file.is_file():
            continue  # file already gone; nothing to track
        conn.execute(uploads.insert().values(
            id=str(uuid.uuid4()),
            user_id=user_id,
            category='avatar',
            original_filename=None,
            stored_path=stored_path,
            content_type=_guess_content_type(file.name),
            size_bytes=file.stat().st_size,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        ))

    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('avatar')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('avatar', sa.String(length=512), nullable=True))

    # Data: copy each user's latest avatar upload back into users.avatar
    conn = op.get_bind()
    rows = conn.execute(sa.text(
        "SELECT user_id, stored_path FROM uploads WHERE category = 'avatar' ORDER BY created_at"
    )).fetchall()
    for user_id, stored_path in rows:  # later rows overwrite earlier ones -> latest wins
        conn.execute(
            sa.text("UPDATE users SET avatar = :avatar WHERE id = :id"),
            {"avatar": URL_PREFIX + stored_path, "id": user_id},
        )

    op.drop_index('ix_uploads_user_id_category', table_name='uploads')
    op.drop_table('uploads')
