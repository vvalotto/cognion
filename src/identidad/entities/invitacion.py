"""Invitación de un Docente para que un Estudiante se registre en su comisión."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

EXPIRACION_DIAS = 7


@dataclass
class Invitacion:
    """Invitación con token único, emitida por un Docente para una Comisión."""

    id: UUID
    comision_id: UUID
    docente_id: UUID
    token: str
    generada_en: datetime
    expira_en: datetime
    usada_en: datetime | None = None

    @staticmethod
    def crear(comision_id: UUID, docente_id: UUID) -> Invitacion:
        """Crea una `Invitacion` nueva con token único y expiración a 7 días (`ADR-012`)."""
        generada_en = datetime.now(UTC)
        return Invitacion(
            id=uuid4(),
            comision_id=comision_id,
            docente_id=docente_id,
            token=secrets.token_urlsafe(32),
            generada_en=generada_en,
            expira_en=generada_en + timedelta(days=EXPIRACION_DIAS),
        )
