"""invitacion_grupal

Revision ID: f7a3c9d15e82
Revises: c4d1f9a27b60
Create Date: 2026-11-08 11:00:00.000000

Agrega a `invitacion` las columnas del link grupal (`US-ADJ-67`): `grupal`, `usos` y `revocada_en`.
Las invitaciones existentes quedan como individuales, sin usos y sin revocar.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7a3c9d15e82"
down_revision: Union[str, Sequence[str], None] = "c4d1f9a27b60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "invitacion",
        sa.Column("grupal", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "invitacion",
        sa.Column("usos", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "invitacion",
        sa.Column("revocada_en", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("invitacion", "revocada_en")
    op.drop_column("invitacion", "usos")
    op.drop_column("invitacion", "grupal")
