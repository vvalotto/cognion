"""pregunta_plantilla

Revision ID: b0e03a73f699
Revises: 295bc74948c3
Create Date: 2026-08-06 17:52:13.697938

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b0e03a73f699"
down_revision: Union[str, Sequence[str], None] = "295bc74948c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "pregunta_plantilla",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("banco_id", sa.UUID(), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("texto", sa.String(length=2000), nullable=False),
        sa.Column("opciones", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("unidad_tematica", sa.String(length=200), nullable=False),
        sa.Column("tema", sa.String(length=200), nullable=False),
        sa.Column("dificultad", sa.String(length=10), nullable=False),
        sa.Column("importancia", sa.String(length=10), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["banco_id"],
            ["banco.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("pregunta_plantilla")
