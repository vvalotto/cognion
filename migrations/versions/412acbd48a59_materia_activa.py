"""materia_activa

Revision ID: 412acbd48a59
Revises: 24b7c1fb0508
Create Date: 2026-09-08 00:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "412acbd48a59"
down_revision: Union[str, Sequence[str], None] = "24b7c1fb0508"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "materia",
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("materia", "activa")
