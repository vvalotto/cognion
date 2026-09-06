"""Controller de la API del BC Analytics (`US-4.1.2`, `US-4.2.1`, `US-4.2.4`).

Primer controller del BC — delega directo en el Use Case, mismo patrón mínimo que
`ActividadesEstudianteController` (`src/actividad_evaluativa`).
"""

from __future__ import annotations

from uuid import UUID

from src.analytics.use_cases.obtener_desempeno_estudiante import (
    DesempenoEstudiante,
    ObtenerDesempenoEstudianteUseCase,
)
from src.analytics.use_cases.obtener_tasa_error_por_tema import (
    ObtenerTasaErrorPorTemaUseCase,
    TasaErrorTema,
)


class AnalyticsController:
    """Adapta requests HTTP de consulta de desempeño al Use Case correspondiente."""

    def __init__(
        self,
        obtener_desempeno_estudiante: ObtenerDesempenoEstudianteUseCase,
        obtener_tasa_error_por_tema: ObtenerTasaErrorPorTemaUseCase,
    ) -> None:
        """Recibe los Use Case de obtención de desempeño y de tasa de error por tema."""
        self._obtener_desempeno_estudiante = obtener_desempeno_estudiante
        self._obtener_tasa_error_por_tema = obtener_tasa_error_por_tema

    async def obtener_mi_desempeno(
        self, estudiante_id: UUID, materia_id: UUID
    ) -> DesempenoEstudiante:
        """Delega la obtención del desempeño en el Use Case correspondiente."""
        return await self._obtener_desempeno_estudiante.execute(estudiante_id, materia_id)

    async def obtener_tasa_error_por_tema(
        self, materia_id: UUID, comision_id: UUID | None
    ) -> list[TasaErrorTema]:
        """Tasa de error por tema de una materia, acotada a una comisión si se indica (RF-17)."""
        return await self._obtener_tasa_error_por_tema.execute(materia_id, comision_id)

    async def obtener_desempeno_de_estudiante(
        self, estudiante_id: UUID, materia_id: UUID
    ) -> DesempenoEstudiante:
        """Desempeño de un Estudiante elegido por el Docente (`US-4.2.1`, RF-16).

        Mismo cálculo que `obtener_mi_desempeno` — el `estudiante_id` viene del path (elegido
        por el Docente) en vez del token, la existencia del Estudiante ya fue validada en el
        router antes de llegar acá.
        """
        return await self._obtener_desempeno_estudiante.execute(estudiante_id, materia_id)
