"""usuario_bloqueo_intentos_fallidos

Revision ID: 4c1b823c7d9f
Revises: 6f523d16bf1c
Create Date: 2026-08-19 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4c1b823c7d9f"
down_revision: Union[str, Sequence[str], None] = "6f523d16bf1c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "usuario",
        sa.Column("bloqueada", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "usuario",
        sa.Column("intentos_fallidos_login", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "usuario",
        sa.Column("intentos_fallidos_password", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("usuario", "intentos_fallidos_password")
    op.drop_column("usuario", "intentos_fallidos_login")
    op.drop_column("usuario", "bloqueada")
