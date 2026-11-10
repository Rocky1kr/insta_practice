"""create users and sessions, add posts.user_id

Revision ID: a1c4e7d2b9f0
Revises: 368ea845ff8c
Create Date: 2026-11-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c4e7d2b9f0'
down_revision: Union[str, Sequence[str], None] = '368ea845ff8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('sessions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # 작성자가 없는 기존 게시물(과 댓글)은 삭제한 뒤 user_id를 필수로 추가
    op.execute('DELETE FROM comments')
    op.execute('DELETE FROM posts')
    op.add_column('posts', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_foreign_key('posts_user_id_fkey', 'posts', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('posts_user_id_fkey', 'posts', type_='foreignkey')
    op.drop_column('posts', 'user_id')
    op.drop_table('sessions')
    op.drop_table('users')
