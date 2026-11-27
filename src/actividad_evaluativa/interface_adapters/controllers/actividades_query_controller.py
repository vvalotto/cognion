"""Controller de la API para consultas de solo lectura sobre actividades (`US-3.4.2`).

Separado de `ActividadesController` (comandos: crear/modificar/cerrar) a propósito — ese
controller ya tiene 3 Use Case inyectados, cerca del umbral de CBO que ya generó CRITICAL en
`US-2.1.2`/`US-2.1.5`/`US-2.1.6`/`US-2.1.7`/`US-2.2.2`. Mismo criterio de separación
command/query que `BancosController` (`US-2.1.7`).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from src.actividad_evaluativa.interface_adapters.presenters.actividad_presenter import (
    ActividadResumenSalida,
    presentar_actividad_resumen,
    presentar_actividades_resumen,
)
from src.actividad_evaluativa.use_cases.listar_actividades import ListarActividadesUseCase
from src.actividad_evaluativa.use_cases.obtener_actividad import ObtenerActividadUseCase


class ActividadesQueryController:
    """Adapta requests HTTP de solo lectura a los Use Case de consulta del BC."""

    def __init__(
        self,
        listar_actividades: ListarActividadesUseCase,
        obtener_actividad: ObtenerActividadUseCase,
    ) -> None:
        """Recibe los Use Case de listado y detalle de actividades."""
        self._listar_actividades = listar_actividades
        self._obtener_actividad = obtener_actividad

    async def listar_actividades(
        self, materia_id: UUID, docente_id: UUID | None = None
    ) -> list[ActividadResumenSalida]:
        """Delega el listado de actividades de una materia en el Use Case correspondiente."""
        resumenes = await self._listar_actividades.execute(materia_id, docente_id)
        return presentar_actividades_resumen(resumenes, datetime.now(UTC))

    async def obtener_actividad(
        self, actividad_id: UUID, docente_id: UUID | None = None
    ) -> ActividadResumenSalida:
        """Delega el detalle de una actividad puntual en el Use Case correspondiente."""
        resumen = await self._obtener_actividad.execute(actividad_id, docente_id)
        return presentar_actividad_resumen(resumen, datetime.now(UTC))
