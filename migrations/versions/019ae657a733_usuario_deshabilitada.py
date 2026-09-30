"""usuario_deshabilitada

Revision ID: 019ae657a733
Revises: 412acbd48a59
Create Date: 2026-09-08 00:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "019ae657a733"
down_revision: Union[str, Sequence[str], None] = "412acbd48a59"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "usuario",
        sa.Column("deshabilitada", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("usuario", "deshabilitada")
