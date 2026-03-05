"""add historial_rendicion

Revision ID: b2c3d4e5f6a7
Revises: 3c5d7e9f1a2b
Create Date: 2026-03-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = '3c5d7e9f1a2b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'historial_rendicion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rendicion_id', sa.Integer(), nullable=False),
        sa.Column('estado_anterior', sa.String(length=20), nullable=False),
        sa.Column('estado_nuevo', sa.String(length=20), nullable=False),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('actor_nombre', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['actor_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['rendicion_id'], ['rendiciones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_historial_rendicion_id'), 'historial_rendicion', ['id'], unique=False)
    op.create_index(op.f('ix_historial_rendicion_rendicion_id'), 'historial_rendicion', ['rendicion_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_historial_rendicion_rendicion_id'), table_name='historial_rendicion')
    op.drop_index(op.f('ix_historial_rendicion_id'), table_name='historial_rendicion')
    op.drop_table('historial_rendicion')
