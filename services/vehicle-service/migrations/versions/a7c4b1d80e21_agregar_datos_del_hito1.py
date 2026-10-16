"""Agregar campos descriptivos y comerciales del modelo Hito 1."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7c4b1d80e21'
down_revision: Union[str, None] = '621f257bdbb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('vehiculos')}
    columns = (
        sa.Column('anio', sa.Integer(), nullable=True),
        sa.Column('color', sa.String(length=50), nullable=True),
        sa.Column('tipo', sa.String(length=20), nullable=True),
        sa.Column('precio_diario', sa.Float(), nullable=True),
        sa.Column('estado', sa.String(length=20), nullable=False, server_default='DISPONIBLE'),
    )
    for column in columns:
        if column.name not in existing:
            op.add_column('vehiculos', column)


def downgrade() -> None:
    existing = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('vehiculos')}
    for column_name in ('estado', 'precio_diario', 'tipo', 'color', 'anio'):
        if column_name in existing:
            op.drop_column('vehiculos', column_name)