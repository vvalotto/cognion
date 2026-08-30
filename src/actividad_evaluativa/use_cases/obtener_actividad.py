"""Caso de uso: detalle de una actividad puntual (`US-3.4.4`, RF-11b)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.errors import ActividadNoExiste
from src.actividad_evaluativa.entities.ports.actividad_query_port import (
    ActividadQueryPort,
    ActividadResumen,
)


class ObtenerActividadUseCase:
    """Consulta de solo lectura sobre una actividad puntual, sin invariantes de dominio."""

    def __init__(self, actividad_query: ActividadQueryPort) -> None:
        """Recibe el puerto de consulta de actividades a usar."""
        self._actividad_query = actividad_query

    async def execute(self, actividad_id: UUID) -> ActividadResumen:
        """Devuelve el resumen de `actividad_id`; lanza `ActividadNoExiste` si no está."""
        actividad = await self._actividad_query.obtener(actividad_id)
        if actividad is None:
            raise ActividadNoExiste(actividad_id)
        return actividad
