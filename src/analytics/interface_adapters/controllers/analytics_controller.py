"""Controller de la API del BC Analytics (`US-4.1.2`).

Primer controller del BC — delega directo en el Use Case, mismo patrón mínimo que
`ActividadesEstudianteController` (`src/actividad_evaluativa`).
"""

from __future__ import annotations

from uuid import UUID

from src.analytics.use_cases.obtener_desempeno_estudiante import (
    DesempenoEstudiante,
    ObtenerDesempenoEstudianteUseCase,
)


class AnalyticsController:
    """Adapta requests HTTP de consulta de desempeño al Use Case correspondiente."""

    def __init__(self, obtener_desempeno_estudiante: ObtenerDesempenoEstudianteUseCase) -> None:
        """Recibe el Use Case de obtención de desempeño del Estudiante."""
        self._obtener_desempeno_estudiante = obtener_desempeno_estudiante

    async def obtener_mi_desempeno(
        self, estudiante_id: UUID, materia_id: UUID
    ) -> DesempenoEstudiante:
        """Delega la obtención del desempeño en el Use Case correspondiente."""
        return await self._obtener_desempeno_estudiante.execute(estudiante_id, materia_id)
