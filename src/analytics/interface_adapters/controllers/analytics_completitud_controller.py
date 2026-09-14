"""Controller de la API del BC Analytics — completitud de una actividad puntual (`US-ADJ-47`).

Tercer controller del BC, separado de `AnalyticsInformesController` — agregar este Use Case
ahí disparó CRITICAL de CBO (11/10) en `designreviewer` local, mismo patrón de separación por
responsabilidad ya aplicado en `US-ADJ-46` (`AnalyticsController`/`AnalyticsInformesController`).
"""

from __future__ import annotations

from uuid import UUID

from src.analytics.use_cases.obtener_completitud_por_actividad import (
    CompletitudPorActividad,
    ObtenerCompletitudPorActividadUseCase,
)


class AnalyticsCompletitudController:
    """Adapta requests HTTP de completitud de actividad al Use Case."""

    def __init__(
        self, obtener_completitud_por_actividad: ObtenerCompletitudPorActividadUseCase
    ) -> None:
        """Recibe el único Use Case de este controller."""
        self._obtener_completitud_por_actividad = obtener_completitud_por_actividad

    async def obtener_completitud_por_actividad(
        self, actividad_id: UUID
    ) -> CompletitudPorActividad:
        """Completitud del roster aplicable de una actividad puntual (RF-23)."""
        return await self._obtener_completitud_por_actividad.execute(actividad_id)
