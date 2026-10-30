from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4a1f7c3b820"
down_revision: Union[str, None] = "d9e7c2a61f04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "vehiculos_externos",
        sa.Column("precio_diario", sa.Float(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("vehiculos_externos", "precio_diario")
