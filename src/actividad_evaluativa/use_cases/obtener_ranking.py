"""Caso de uso: consultar el ranking de la sesión en vivo (US-6.2.8, RF-10)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
    EstadoSesionEnVivo,
)
from src.actividad_evaluativa.entities.errors import RankingNoDisponible, SesionNoExiste
from src.actividad_evaluativa.entities.ports.event_store_port import EventStorePort
from src.actividad_evaluativa.entities.ports.proyecciones_en_vivo_port import (
    ParticipanteEnRanking,
    ProyeccionesEnVivoQueryPort,
)

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"


class ObtenerRankingUseCase:
    """Lee el ranking; el Estudiante solo lo ve con la sesión `Finalizada` (§17 punto 10)."""

    def __init__(
        self, event_store: EventStorePort, proyecciones: ProyeccionesEnVivoQueryPort
    ) -> None:
        """Recibe el event store y la lectura de proyecciones."""
        self._event_store = event_store
        self._proyecciones = proyecciones

    async def execute(self, sesion_id: UUID, es_estudiante: bool) -> list[ParticipanteEnRanking]:
        """Devuelve el ranking ordenado; levanta `SesionNoExiste` o `RankingNoDisponible`."""
        eventos = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos:
            raise SesionNoExiste(sesion_id)
        sesion = ActividadEvaluativaEnVivo.reconstruir(eventos)
        if es_estudiante and sesion.estado != EstadoSesionEnVivo.FINALIZADA:
            raise RankingNoDisponible(sesion_id)
        return await self._proyecciones.ranking(sesion_id)
