"""Caso de uso: consulta del último link de invitación grupal de una comisión (`US-ADJ-67`)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from src.identidad.entities.invitacion import EstadoInvitacion
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.entities.ports.invitacion_repository_port import InvitacionRepositoryPort
from src.identidad.use_cases.autorizacion_comision import exigir_docente_asignado


@dataclass(frozen=True)
class InvitacionGrupalEstado:
    """Estado del último link grupal; el `token` solo viaja mientras el link está vigente."""

    id: UUID
    estado: EstadoInvitacion
    token: str | None
    generada_en: datetime
    expira_en: datetime
    usos: int


class ObtenerUltimaInvitacionGrupalUseCase:
    """Devuelve el último link grupal de la comisión para mostrarlo al volver a la pantalla."""

    def __init__(
        self,
        comision_repositorio: ComisionRepositoryPort,
        invitacion_repositorio: InvitacionRepositoryPort,
    ) -> None:
        """Recibe los repositorios de comisiones e invitaciones."""
        self._comision_repositorio = comision_repositorio
        self._invitacion_repositorio = invitacion_repositorio

    async def execute(
        self, comision_id: UUID, solicitante_id: UUID
    ) -> InvitacionGrupalEstado | None:
        """Devuelve el estado del último link grupal, o `None` si la comisión nunca generó uno.

        Lanza `ComisionNoExiste` o `ComisionNoAutorizada` (el Docente no está asignado).
        """
        await exigir_docente_asignado(self._comision_repositorio, comision_id, solicitante_id)

        invitacion = await self._invitacion_repositorio.obtener_ultima_grupal(comision_id)
        if invitacion is None:
            return None
        estado = invitacion.estado(datetime.now(UTC))
        return InvitacionGrupalEstado(
            id=invitacion.id,
            estado=estado,
            token=invitacion.token if estado is EstadoInvitacion.VIGENTE else None,
            generada_en=invitacion.generada_en,
            expira_en=invitacion.expira_en,
            usos=invitacion.usos,
        )
