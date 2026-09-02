"""Caso de uso: listado de actividades de una materia (`US-3.4.2`, RF-11)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.ports.actividad_query_port import (
    ActividadQueryPort,
    ActividadResumen,
)


class ListarActividadesUseCase:
    """Delega el listado en el puerto de consulta, sin lógica propia."""

    def __init__(self, actividad_query: ActividadQueryPort) -> None:
        """Recibe el puerto de consulta de actividades a usar."""
        self._actividad_query = actividad_query

    async def execute(self, materia_id: UUID) -> list[ActividadResumen]:
        """Devuelve el resumen de cada actividad de `materia_id`."""
        return await self._actividad_query.listar_por_materia(materia_id)
