"""Unify the vehicle migration heads."""
from typing import Sequence, Union


revision: str = "d9e7c2a61f04"
down_revision: Union[str, Sequence[str], None] = (
    "b8c9d0e1f2a3",
    "c3f7b2e5a914",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
