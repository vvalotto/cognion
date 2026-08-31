"""Controller de la API para el listado de actividades visibles del Estudiante (`US-3.4.5`).

Separado de `ActividadesQueryController` (consulta del lado Docente, `US-3.4.2`) a propósito —
evita sumarle un tercer actor a un controller ya usado por dos Use Case, mismo criterio de
separación command/query que motivó `ActividadesQueryController` en primer lugar.
"""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.use_cases.listar_actividades_visibles import (
    ActividadVisible,
    ListarActividadesVisiblesUseCase,
)


class ActividadesEstudianteController:
    """Adapta requests HTTP del Estudiante al Use Case de listado de actividades visibles."""

    def __init__(self, listar_actividades_visibles: ListarActividadesVisiblesUseCase) -> None:
        """Recibe el Use Case de listado de actividades visibles del Estudiante."""
        self._listar_actividades_visibles = listar_actividades_visibles

    async def listar_actividades_visibles(
        self, materia_id: UUID, estudiante_id: UUID
    ) -> list[ActividadVisible]:
        """Delega el listado de actividades visibles en el Use Case correspondiente."""
        return await self._listar_actividades_visibles.execute(materia_id, estudiante_id)
