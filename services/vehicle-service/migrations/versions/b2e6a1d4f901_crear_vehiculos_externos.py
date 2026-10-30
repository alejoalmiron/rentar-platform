from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2e6a1d4f901"
down_revision: Union[str, None] = "a7c4b1d80e21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "vehiculos_externos" not in inspector.get_table_names():
        op.create_table(
            "vehiculos_externos",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("vehiculo_externo_id", sa.String(length=36), nullable=False),
            sa.Column("cliente_id", sa.String(length=36), nullable=False),
            sa.Column("marca", sa.String(length=50), nullable=False),
            sa.Column("modelo", sa.String(length=50), nullable=False),
            sa.Column("patente", sa.String(length=20), nullable=False),
            sa.Column("anio", sa.Integer(), nullable=True),
            sa.Column("color", sa.String(length=50), nullable=True),
            sa.Column("tipo", sa.String(length=20), nullable=True),
            sa.Column("estado", sa.String(length=20), nullable=False, server_default="PENDIENTE"),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("patente_validada", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("titularidad_validada", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("vehiculo_externo_id"),
            sa.UniqueConstraint("patente"),
        )
        op.create_index(
            op.f("ix_vehiculos_externos_id"),
            "vehiculos_externos",
            ["id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_vehiculos_externos_vehiculo_externo_id"),
            "vehiculos_externos",
            ["vehiculo_externo_id"],
            unique=False,
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "vehiculos_externos" in inspector.get_table_names():
        op.drop_index(op.f("ix_vehiculos_externos_vehiculo_externo_id"), table_name="vehiculos_externos")
        op.drop_index(op.f("ix_vehiculos_externos_id"), table_name="vehiculos_externos")
        op.drop_table("vehiculos_externos")
