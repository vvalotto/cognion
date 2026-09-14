"""Controller de la API del BC Analytics — desempeño individual del Estudiante.

`US-4.1.2`, `US-4.2.1`, `US-ADJ-45`. Separado de `AnalyticsInformesController`
(`analytics_informes_controller.py`, `US-ADJ-46`) — mismo criterio de separación por
responsabilidad ya aplicado en Incremento 2 (`BancosController`/`PreguntasController`,
`CuentasController`/`UsuariosController`) para no repetir el CRITICAL de CBO que salió al
mezclar demasiados Use Case en un solo controller.
"""

from __future__ import annotations

from uuid import UUID

from src.analytics.use_cases.obtener_desempeno_estudiante import (
    DesempenoEstudiante,
    ObtenerDesempenoEstudianteUseCase,
)
from src.analytics.use_cases.obtener_evolucion_temporal_estudiante import (
    EvolucionTemporalPunto,
    ObtenerEvolucionTemporalEstudianteUseCase,
)


class AnalyticsController:
    """Adapta requests HTTP de consulta de desempeño individual al Use Case correspondiente."""

    def __init__(
        self,
        obtener_desempeno_estudiante: ObtenerDesempenoEstudianteUseCase,
        obtener_evolucion_temporal_estudiante: ObtenerEvolucionTemporalEstudianteUseCase,
    ) -> None:
        """Recibe los Use Case de desempeño y evolución temporal individuales."""
        self._obtener_desempeno_estudiante = obtener_desempeno_estudiante
        self._obtener_evolucion_temporal_estudiante = obtener_evolucion_temporal_estudiante

    async def obtener_mi_desempeno(
        self, estudiante_id: UUID, materia_id: UUID
    ) -> DesempenoEstudiante:
        """Delega la obtención del desempeño en el Use Case correspondiente."""
        return await self._obtener_desempeno_estudiante.execute(estudiante_id, materia_id)

    async def obtener_desempeno_de_estudiante(
        self, estudiante_id: UUID, materia_id: UUID
    ) -> DesempenoEstudiante:
        """Desempeño de un Estudiante elegido por el Docente (`US-4.2.1`, RF-16).

        Mismo cálculo que `obtener_mi_desempeno` — el `estudiante_id` viene del path (elegido
        por el Docente) en vez del token, la existencia del Estudiante ya fue validada en el
        router antes de llegar acá.
        """
        return await self._obtener_desempeno_estudiante.execute(estudiante_id, materia_id)

    async def obtener_evolucion_temporal_estudiante(
        self, estudiante_id: UUID, materia_id: UUID
    ) -> list[EvolucionTemporalPunto]:
        """Evolución temporal individual de un estudiante (`US-ADJ-45`, RF-21)."""
        return await self._obtener_evolucion_temporal_estudiante.execute(estudiante_id, materia_id)
