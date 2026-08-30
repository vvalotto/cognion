"""Controller de la API para consultas de solo lectura sobre actividades (`US-3.4.2`).

Separado de `ActividadesController` (comandos: crear/modificar/cerrar) a propósito — ese
controller ya tiene 3 Use Case inyectados, cerca del umbral de CBO que ya generó CRITICAL en
`US-2.1.2`/`US-2.1.5`/`US-2.1.6`/`US-2.1.7`/`US-2.2.2`. Mismo criterio de separación
command/query que `BancosController` (`US-2.1.7`).
"""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.ports.actividad_query_port import ActividadResumen
from src.actividad_evaluativa.use_cases.listar_actividades import ListarActividadesUseCase


class ActividadesQueryController:
    """Adapta requests HTTP de solo lectura a los Use Case de consulta del BC."""

    def __init__(self, listar_actividades: ListarActividadesUseCase) -> None:
        """Recibe el Use Case de listado de actividades."""
        self._listar_actividades = listar_actividades

    async def listar_actividades(self, materia_id: UUID) -> list[ActividadResumen]:
        """Delega el listado de actividades de una materia en el Use Case correspondiente."""
        return await self._listar_actividades.execute(materia_id)
