"""usuario_bloqueada_hasta

Revision ID: c4d1f9a27b60
Revises: a6c2d4f8b1e3
Create Date: 2026-10-03 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d1f9a27b60"
down_revision: Union[str, Sequence[str], None] = "a6c2d4f8b1e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agrega `usuario.bloqueada_hasta` (bloqueo temporal del último Administrador, INV-ID-21)."""
    op.add_column("usuario", sa.Column("bloqueada_hasta", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Quita `usuario.bloqueada_hasta`."""
    op.drop_column("usuario", "bloqueada_hasta")
