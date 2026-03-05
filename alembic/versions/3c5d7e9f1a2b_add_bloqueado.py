"""add bloqueado to usuarios

Revision ID: 3c5d7e9f1a2b
Revises: 7ea1262af18c
Create Date: 2026-03-03 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '3c5d7e9f1a2b'
down_revision = '7ea1262af18c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('bloqueado', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('usuarios', 'bloqueado')
