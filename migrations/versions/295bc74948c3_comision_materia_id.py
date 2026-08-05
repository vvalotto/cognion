"""comision_materia_id

Revision ID: 295bc74948c3
Revises: 099d86aa5d0d
Create Date: 2026-08-05 11:57:41.187345

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "295bc74948c3"
down_revision: Union[str, Sequence[str], None] = "099d86aa5d0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: `comision.materia` (string) -> `comision.materia_id` (UUID, US-2.1.2)."""
    op.add_column("comision", sa.Column("materia_id", sa.UUID(), nullable=True))
    op.execute(
        "UPDATE comision SET materia_id = materia.id "
        "FROM materia WHERE comision.materia = materia.nombre"
    )
    op.alter_column("comision", "materia_id", nullable=False)
    op.drop_column("comision", "materia")


def downgrade() -> None:
    """Downgrade schema: revierte `materia_id` a `materia` (string) por nombre."""
    op.add_column(
        "comision", sa.Column("materia", sa.VARCHAR(length=200), nullable=True)
    )
    op.execute(
        "UPDATE comision SET materia = materia.nombre "
        "FROM materia WHERE comision.materia_id = materia.id"
    )
    op.alter_column("comision", "materia", nullable=False)
    op.drop_column("comision", "materia_id")
