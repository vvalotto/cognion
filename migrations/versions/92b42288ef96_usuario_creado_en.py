"""usuario_creado_en

Revision ID: 92b42288ef96
Revises: 4c1b823c7d9f
Create Date: 2026-08-19 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "92b42288ef96"
down_revision: Union[str, Sequence[str], None] = "4c1b823c7d9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "usuario",
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("usuario", "creado_en")
