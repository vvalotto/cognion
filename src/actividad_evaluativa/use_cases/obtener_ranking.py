"""Caso de uso: consultar el ranking de la sesión en vivo (US-6.2.8, RF-10)."""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
    EstadoSesionEnVivo,
)
from src.actividad_evaluativa.entities.errors import RankingNoDisponible, SesionNoExiste
from src.actividad_evaluativa.entities.ports.estudiante_consulta_port import (
    EstudianteConsultaPort,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventStorePort
from src.actividad_evaluativa.entities.ports.proyecciones_en_vivo_port import (
    ParticipanteEnRanking,
    ProyeccionesEnVivoQueryPort,
)
from src.actividad_evaluativa.use_cases._resolucion_nombres import resolver_nombres

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"


class ObtenerRankingUseCase:
    """Lee el ranking; el Estudiante solo lo ve con la sesión `Finalizada` (§17 punto 10)."""

    def __init__(
        self,
        event_store: EventStorePort,
        proyecciones: ProyeccionesEnVivoQueryPort,
        estudiante_consulta: EstudianteConsultaPort,
    ) -> None:
        """Recibe el event store, la lectura de proyecciones y la consulta de Identidad."""
        self._event_store = event_store
        self._proyecciones = proyecciones
        self._estudiante_consulta = estudiante_consulta

    async def execute(self, sesion_id: UUID, es_estudiante: bool) -> list[ParticipanteEnRanking]:
        """Devuelve el ranking ordenado con `nombre` resuelto.

        Levanta `SesionNoExiste` o `RankingNoDisponible`.
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos:
            raise SesionNoExiste(sesion_id)
        sesion = ActividadEvaluativaEnVivo.reconstruir(eventos)
        if es_estudiante and sesion.estado != EstadoSesionEnVivo.FINALIZADA:
            raise RankingNoDisponible(sesion_id)
        ranking = await self._proyecciones.ranking(sesion_id)
        nombres = await resolver_nombres(
            self._estudiante_consulta, (r.estudiante_id for r in ranking)
        )
        return [replace(r, nombre=nombres[r.estudiante_id]) for r in ranking]
