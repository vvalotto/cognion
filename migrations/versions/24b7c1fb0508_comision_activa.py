"""comision_activa

Revision ID: 24b7c1fb0508
Revises: 9244e3956c69
Create Date: 2026-09-08 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "24b7c1fb0508"
down_revision: Union[str, Sequence[str], None] = "9244e3956c69"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "comision",
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("comision", "activa")
