"""Caso de uso: el Docente lista los participantes de la sala de espera (US-6.2.8)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.errors import SesionNoExiste
from src.actividad_evaluativa.entities.ports.event_store_port import EventStorePort
from src.actividad_evaluativa.entities.ports.participantes_sesion_query_port import (
    ParticipanteResumen,
    ParticipantesSesionQueryPort,
)

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"


class ListarParticipantesUseCase:
    """Lee el read model de participantes de una sesión existente."""

    def __init__(
        self, event_store: EventStorePort, participantes: ParticipantesSesionQueryPort
    ) -> None:
        """Recibe el event store y la consulta de participantes."""
        self._event_store = event_store
        self._participantes = participantes

    async def execute(self, sesion_id: UUID) -> list[ParticipanteResumen]:
        """Devuelve los Estudiantes unidos en orden de unión; levanta `SesionNoExiste`."""
        if not await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id):
            raise SesionNoExiste(sesion_id)
        return await self._participantes.listar(sesion_id)
