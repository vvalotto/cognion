"""read_models_sesion_en_vivo

Revision ID: a6c2d4f8b1e3
Revises: e31e7dfcab3a
Create Date: 2026-09-20 09:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a6c2d4f8b1e3"
down_revision: Union[str, Sequence[str], None] = "e31e7dfcab3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea los read models `ranking_por_sesion` y `distribucion_por_pregunta` (US-6.2.3)."""
    op.create_table(
        "ranking_por_sesion",
        sa.Column("sesion_id", sa.UUID(), nullable=False),
        sa.Column("estudiante_id", sa.UUID(), nullable=False),
        sa.Column("puntaje_acumulado", sa.Integer(), nullable=False),
        sa.Column("ultima_actualizacion", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("sesion_id", "estudiante_id"),
    )
    op.create_table(
        "distribucion_por_pregunta",
        sa.Column("sesion_id", sa.UUID(), nullable=False),
        sa.Column("pregunta_id", sa.UUID(), nullable=False),
        sa.Column("opcion", sa.String(length=50), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("sesion_id", "pregunta_id", "opcion"),
    )


def downgrade() -> None:
    """Elimina ambos read models."""
    op.drop_table("distribucion_por_pregunta")
    op.drop_table("ranking_por_sesion")
