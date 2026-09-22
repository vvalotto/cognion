"""Caso de uso: el Docente lista los participantes de la sala de espera (US-6.2.8)."""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from src.actividad_evaluativa.entities.errors import SesionNoExiste
from src.actividad_evaluativa.entities.ports.estudiante_consulta_port import (
    EstudianteConsultaPort,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventStorePort
from src.actividad_evaluativa.entities.ports.participantes_sesion_query_port import (
    ParticipanteResumen,
    ParticipantesSesionQueryPort,
)
from src.actividad_evaluativa.use_cases._resolucion_nombres import resolver_nombres

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"


class ListarParticipantesUseCase:
    """Lee el read model de participantes de una sesión existente."""

    def __init__(
        self,
        event_store: EventStorePort,
        participantes: ParticipantesSesionQueryPort,
        estudiante_consulta: EstudianteConsultaPort,
    ) -> None:
        """Recibe el event store, la consulta de participantes y la consulta de Identidad."""
        self._event_store = event_store
        self._participantes = participantes
        self._estudiante_consulta = estudiante_consulta

    async def execute(self, sesion_id: UUID) -> list[ParticipanteResumen]:
        """Devuelve los Estudiantes unidos en orden de unión, con `nombre` resuelto.

        Levanta `SesionNoExiste`.
        """
        if not await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id):
            raise SesionNoExiste(sesion_id)
        participantes = await self._participantes.listar(sesion_id)
        nombres = await resolver_nombres(
            self._estudiante_consulta, (p.estudiante_id for p in participantes)
        )
        return [replace(p, nombre=nombres[p.estudiante_id]) for p in participantes]
