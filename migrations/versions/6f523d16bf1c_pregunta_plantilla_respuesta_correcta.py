"""pregunta_plantilla_respuesta_correcta

Revision ID: 6f523d16bf1c
Revises: b0e03a73f699
Create Date: 2026-08-08 10:34:39.638146

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6f523d16bf1c"
down_revision: Union[str, Sequence[str], None] = "b0e03a73f699"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "pregunta_plantilla",
        sa.Column("respuesta_correcta", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("pregunta_plantilla", "respuesta_correcta")
