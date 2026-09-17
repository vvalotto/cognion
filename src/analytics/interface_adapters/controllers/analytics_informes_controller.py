"""Controller de la API del BC Analytics — informes agregados de comisión/materia.

`US-4.2.4`, `US-ADJ-44`, `US-ADJ-45`, `US-ADJ-46`. Separado de `AnalyticsController`
(desempeño individual del Estudiante) — mismo criterio de separación por responsabilidad ya
aplicado en Incremento 2 (`BancosController`/`PreguntasController`,
`CuentasController`/`UsuariosController`): agregar el 6° Use Case (`US-ADJ-46`) al controller
único disparó CRITICAL de CBO (13/10) en el pre-push gate. `US-ADJ-47` repitió el mismo patrón
al intentar agregar un 5° Use Case acá (CBO 11/10) — resuelto con un tercer controller,
`AnalyticsCompletitudController`, en vez de forzarlo en este.
"""

from __future__ import annotations

from uuid import UUID

from src.analytics.use_cases.obtener_desempeno_por_comision import (
    DesempenoComisionFila,
    ObtenerDesempenoPorComisionUseCase,
)
from src.analytics.use_cases.obtener_evolucion_temporal_comision import (
    EvolucionTemporalComisionPunto,
    ObtenerEvolucionTemporalComisionUseCase,
)
from src.analytics.use_cases.obtener_ranking_preguntas_falladas import (
    ObtenerRankingPreguntasFalladasUseCase,
    RankingPreguntaFallada,
)
from src.analytics.use_cases.obtener_tasa_error_por_tema import (
    ObtenerTasaErrorPorTemaUseCase,
    TasaErrorTema,
)


class AnalyticsInformesController:
    """Adapta requests HTTP de informes agregados de comisión/materia al Use Case."""

    def __init__(
        self,
        obtener_tasa_error_por_tema: ObtenerTasaErrorPorTemaUseCase,
        obtener_desempeno_por_comision: ObtenerDesempenoPorComisionUseCase,
        obtener_evolucion_temporal_comision: ObtenerEvolucionTemporalComisionUseCase,
        obtener_ranking_preguntas_falladas: ObtenerRankingPreguntasFalladasUseCase,
    ) -> None:
        """Recibe los 4 Use Case de informes agregados del BC."""
        self._obtener_tasa_error_por_tema = obtener_tasa_error_por_tema
        self._obtener_desempeno_por_comision = obtener_desempeno_por_comision
        self._obtener_evolucion_temporal_comision = obtener_evolucion_temporal_comision
        self._obtener_ranking_preguntas_falladas = obtener_ranking_preguntas_falladas

    async def obtener_tasa_error_por_tema(
        self, materia_id: UUID, comision_id: UUID | None
    ) -> list[TasaErrorTema]:
        """Tasa de error por tema de una materia, acotada a una comisión si se indica (RF-17)."""
        return await self._obtener_tasa_error_por_tema.execute(materia_id, comision_id)

    async def obtener_desempeno_por_comision(
        self, materia_id: UUID, comision_id: UUID
    ) -> list[DesempenoComisionFila]:
        """Desempeño de todos los estudiantes de una comisión (`US-ADJ-44`, RF-20)."""
        return await self._obtener_desempeno_por_comision.execute(materia_id, comision_id)

    async def obtener_evolucion_temporal_comision(
        self, materia_id: UUID, comision_id: UUID
    ) -> list[EvolucionTemporalComisionPunto]:
        """Evolución temporal promedio de una comisión (`US-ADJ-45`, RF-21)."""
        return await self._obtener_evolucion_temporal_comision.execute(materia_id, comision_id)

    async def obtener_ranking_preguntas_falladas(
        self, materia_id: UUID, comision_id: UUID | None
    ) -> list[RankingPreguntaFallada]:
        """Ranking de preguntas más falladas de una materia (`US-ADJ-46`, RF-22)."""
        return await self._obtener_ranking_preguntas_falladas.execute(materia_id, comision_id)
