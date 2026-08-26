"""Controller de la API para operaciones sobre actividades de período abierto."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import (
    ActividadEvaluativaPeriodoAbierto,
)
from src.actividad_evaluativa.entities.eventos import ActividadEvaluativaCreada
from src.actividad_evaluativa.use_cases.crear_actividad_periodo_abierto import (
    CrearActividadPeriodoAbiertoUseCase,
)


class ActividadesController:
    """Adapta requests HTTP al caso de uso de alta de actividades de período abierto."""

    def __init__(self, crear_actividad: CrearActividadPeriodoAbiertoUseCase) -> None:
        """Recibe el caso de uso de creación de actividades."""
        self._crear_actividad = crear_actividad

    async def crear_actividad(
        self,
        materia_id: UUID,
        fecha_apertura: datetime,
        fecha_cierre: datetime,
        cantidad_preguntas: int,
        cantidad_intentos_permitidos: int,
    ) -> tuple[ActividadEvaluativaPeriodoAbierto, ActividadEvaluativaCreada]:
        """Delega la creación de la actividad en el caso de uso correspondiente."""
        return await self._crear_actividad.execute(
            materia_id,
            fecha_apertura,
            fecha_cierre,
            cantidad_preguntas,
            cantidad_intentos_permitidos,
        )
