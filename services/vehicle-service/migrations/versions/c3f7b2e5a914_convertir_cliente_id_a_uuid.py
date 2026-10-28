from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3f7b2e5a914"
down_revision: Union[str, None] = "b2e6a1d4f901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "vehiculos_externos" in inspector.get_table_names():
        columns = {
            column["name"]: column
            for column in inspector.get_columns("vehiculos_externos")
        }
        cliente_id = columns.get("cliente_id")
        if cliente_id and isinstance(cliente_id["type"], sa.Integer):
            op.alter_column(
                "vehiculos_externos",
                "cliente_id",
                existing_type=sa.Integer(),
                type_=sa.String(length=36),
                existing_nullable=False,
            )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "vehiculos_externos" in inspector.get_table_names():
        columns = {
            column["name"]: column
            for column in inspector.get_columns("vehiculos_externos")
        }
        cliente_id = columns.get("cliente_id")
        if cliente_id and isinstance(cliente_id["type"], sa.String):
            op.alter_column(
                "vehiculos_externos",
                "cliente_id",
                existing_type=sa.String(length=36),
                type_=sa.Integer(),
                existing_nullable=False,
            )
