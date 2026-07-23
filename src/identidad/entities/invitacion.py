"""Invitación de un Docente para que un Estudiante se registre en su comisión."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from src.identidad.entities.errors import InvitacionNoValida

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

    def es_vigente(self, ahora: datetime) -> bool:
        """Indica si la invitación puede aceptarse: no vencida y no usada (INV-ID-01, INV-ID-03)."""
        return self.usada_en is None and ahora < self.expira_en

    def aceptar(self, ahora: datetime) -> None:
        """Marca la invitación como usada.

        Lanza `InvitacionNoValida` si ya no está vigente (INV-ID-01, INV-ID-03).
        """
        if not self.es_vigente(ahora):
            raise InvitacionNoValida(self.token)
        self.usada_en = ahora
