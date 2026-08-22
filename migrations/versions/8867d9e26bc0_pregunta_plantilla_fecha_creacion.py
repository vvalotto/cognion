"""pregunta_plantilla_fecha_creacion

Revision ID: 8867d9e26bc0
Revises: 92b42288ef96
Create Date: 2026-08-22 14:30:43.287116

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8867d9e26bc0"
down_revision: Union[str, Sequence[str], None] = "92b42288ef96"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "pregunta_plantilla",
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("pregunta_plantilla", "fecha_creacion")
