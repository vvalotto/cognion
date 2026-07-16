"""fundacion tecnica - primera migracion vacia

Revision ID: 696c5efea732
Revises:
Create Date: 2026-07-16 09:33:09.342539

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "696c5efea732"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
