"""Invitación de un Docente para que Estudiantes se registren en su comisión.

Hay dos clases sobre el mismo agregado (`ADR-012`, `ADR-027`): la **individual** (un solo uso,
7 días) y la **grupal** (`US-ADJ-67`), que toda la comisión puede usar hasta que venza o el
Docente la desactive.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4

from src.identidad.entities.errors import (
    DuracionInvitacionInvalida,
    InvitacionRevocada,
    InvitacionVencida,
    InvitacionYaUsada,
)

EXPIRACION_DIAS = 7
DURACIONES_GRUPALES_MINUTOS = (15, 60, 1440)
DURACION_GRUPAL_POR_DEFECTO_MINUTOS = 60


class EstadoInvitacion(StrEnum):
    """Estado de una invitación en un momento dado."""

    VIGENTE = "vigente"
    VENCIDA = "vencida"
    REVOCADA = "revocada"
    USADA = "usada"


@dataclass
class Invitacion:
    """Invitación con token único, emitida por un Docente para una Comisión.

    `grupal` distingue el link para toda la clase del individual; `usos` cuenta los registros hechos
    con ella y `revocada_en` marca el momento en que el Docente la desactivó o la reemplazó.
    """

    id: UUID
    comision_id: UUID
    docente_id: UUID
    token: str
    generada_en: datetime
    expira_en: datetime
    usada_en: datetime | None = None
    grupal: bool = False
    usos: int = 0
    revocada_en: datetime | None = None

    @staticmethod
    def crear(comision_id: UUID, docente_id: UUID) -> Invitacion:
        """Crea una `Invitacion` individual con token único y expiración a 7 días (`ADR-012`)."""
        generada_en = datetime.now(UTC)
        return Invitacion(
            id=uuid4(),
            comision_id=comision_id,
            docente_id=docente_id,
            token=secrets.token_urlsafe(32),
            generada_en=generada_en,
            expira_en=generada_en + timedelta(days=EXPIRACION_DIAS),
        )

    @staticmethod
    def crear_grupal(
        comision_id: UUID,
        docente_id: UUID,
        duracion_minutos: int = DURACION_GRUPAL_POR_DEFECTO_MINUTOS,
    ) -> Invitacion:
        """Crea un link grupal que vence en `duracion_minutos` (15, 60 o 1440; `US-ADJ-67`).

        Lanza `DuracionInvitacionInvalida` si la duración no es una de las elegibles.
        """
        if duracion_minutos not in DURACIONES_GRUPALES_MINUTOS:
            raise DuracionInvitacionInvalida(duracion_minutos, DURACIONES_GRUPALES_MINUTOS)
        generada_en = datetime.now(UTC)
        return Invitacion(
            id=uuid4(),
            comision_id=comision_id,
            docente_id=docente_id,
            token=secrets.token_urlsafe(32),
            generada_en=generada_en,
            expira_en=generada_en + timedelta(minutes=duracion_minutos),
            grupal=True,
        )

    def estado(self, ahora: datetime) -> EstadoInvitacion:
        """Devuelve el estado en `ahora`: revocada, usada (solo individual), vencida o vigente."""
        if self.revocada_en is not None:
            return EstadoInvitacion.REVOCADA
        if self.usada_en is not None:
            return EstadoInvitacion.USADA
        if ahora >= self.expira_en:
            return EstadoInvitacion.VENCIDA
        return EstadoInvitacion.VIGENTE

    def es_vigente(self, ahora: datetime) -> bool:
        """Indica si la invitación puede aceptarse: vigente en `ahora` (INV-ID-01, INV-ID-03)."""
        return self.estado(ahora) is EstadoInvitacion.VIGENTE

    def verificar_vigente(self, ahora: datetime) -> None:
        """Lanza el rechazo específico si la invitación no puede aceptarse.

        Lanza `InvitacionRevocada` si el Docente la desactivó, `InvitacionYaUsada` si es individual
        y ya se usó (INV-ID-01), o `InvitacionVencida` si `ahora >= expira_en` (INV-ID-03). No lanza
        nada si es vigente.
        """
        estado = self.estado(ahora)
        if estado is EstadoInvitacion.REVOCADA:
            raise InvitacionRevocada(self.token)
        if estado is EstadoInvitacion.USADA:
            raise InvitacionYaUsada(self.token)
        if estado is EstadoInvitacion.VENCIDA:
            raise InvitacionVencida(self.token)

    def aceptar(self, ahora: datetime) -> None:
        """Registra un uso: la individual queda usada; la grupal sigue vigente.

        Lanza el rechazo que corresponda si ya no está vigente — ver `verificar_vigente`. El
        contador `usos` de la grupal no se toca acá: con registros simultáneos lo suma la base de
        datos en una sola sentencia (`incrementar_usos`); un contador en memoria perdería cuentas.
        """
        self.verificar_vigente(ahora)
        if not self.grupal:
            self.usada_en = ahora
            self.usos = 1

    def revocar(self, ahora: datetime) -> bool:
        """Desactiva la invitación si está vigente; devuelve si hubo un cambio (idempotente)."""
        if not self.es_vigente(ahora):
            return False
        self.revocada_en = ahora
        return True
