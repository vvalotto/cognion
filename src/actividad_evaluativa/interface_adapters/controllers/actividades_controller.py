"""Controller de la API para operaciones sobre actividades de período abierto."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import (
    ActividadEvaluativaPeriodoAbierto,
)
from src.actividad_evaluativa.entities.eventos import ActividadEvaluativaCreada
from src.actividad_evaluativa.use_cases.cerrar_actividad import CerrarActividadUseCase
from src.actividad_evaluativa.use_cases.crear_actividad_periodo_abierto import (
    CrearActividadPeriodoAbiertoUseCase,
)
from src.actividad_evaluativa.use_cases.modificar_periodo_disponibilidad import (
    ModificarPeriodoDisponibilidadUseCase,
)


class ActividadesController:
    """Adapta requests HTTP a los casos de uso sobre actividades de período abierto."""

    def __init__(
        self,
        crear_actividad: CrearActividadPeriodoAbiertoUseCase,
        modificar_periodo: ModificarPeriodoDisponibilidadUseCase,
        cerrar_actividad: CerrarActividadUseCase,
    ) -> None:
        """Recibe los casos de uso de creación, modificación y cierre de actividades."""
        self._crear_actividad = crear_actividad
        self._modificar_periodo = modificar_periodo
        self._cerrar_actividad = cerrar_actividad

    async def crear_actividad(
        self,
        materia_id: UUID,
        fecha_apertura: datetime,
        fecha_cierre: datetime,
        cantidad_preguntas: int,
        cantidad_intentos_permitidos: int,
        titulo: str = "",
    ) -> tuple[ActividadEvaluativaPeriodoAbierto, ActividadEvaluativaCreada]:
        """Delega la creación de la actividad en el caso de uso correspondiente."""
        return await self._crear_actividad.execute(
            materia_id,
            fecha_apertura,
            fecha_cierre,
            cantidad_preguntas,
            cantidad_intentos_permitidos,
            titulo,
        )

    async def modificar_periodo_disponibilidad(
        self, actividad_id: UUID, nueva_fecha_cierre: datetime
    ) -> ActividadEvaluativaPeriodoAbierto:
        """Delega la modificación del período en el caso de uso correspondiente (RF-11b)."""
        return await self._modificar_periodo.execute(actividad_id, nueva_fecha_cierre)

    async def cerrar_actividad(self, actividad_id: UUID) -> ActividadEvaluativaPeriodoAbierto:
        """Delega el cierre manual de la actividad en el caso de uso correspondiente (RF-11b)."""
        return await self._cerrar_actividad.execute(actividad_id)
