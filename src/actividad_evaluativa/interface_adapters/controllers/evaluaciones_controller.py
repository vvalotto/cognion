"""Controller de la API para operaciones sobre evaluaciones de un Estudiante."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.evaluacion import Evaluacion, Respuesta
from src.actividad_evaluativa.use_cases.finalizar_evaluacion import FinalizarEvaluacionUseCase
from src.actividad_evaluativa.use_cases.iniciar_evaluacion import IniciarEvaluacionUseCase
from src.actividad_evaluativa.use_cases.reanudar_evaluacion import ReanudarEvaluacionUseCase
from src.actividad_evaluativa.use_cases.registrar_respuesta import RegistrarRespuestaUseCase
from src.actividad_evaluativa.use_cases.suspender_evaluacion import SuspenderEvaluacionUseCase


class EvaluacionesController:
    """Adapta requests HTTP a los casos de uso sobre evaluaciones de un Estudiante."""

    def __init__(
        self,
        iniciar_evaluacion: IniciarEvaluacionUseCase,
        registrar_respuesta: RegistrarRespuestaUseCase,
        suspender_evaluacion: SuspenderEvaluacionUseCase,
        reanudar_evaluacion: ReanudarEvaluacionUseCase,
        finalizar_evaluacion: FinalizarEvaluacionUseCase,
    ) -> None:
        """Recibe los casos de uso sobre evaluaciones de un Estudiante."""
        self._iniciar_evaluacion = iniciar_evaluacion
        self._registrar_respuesta = registrar_respuesta
        self._suspender_evaluacion = suspender_evaluacion
        self._reanudar_evaluacion = reanudar_evaluacion
        self._finalizar_evaluacion = finalizar_evaluacion

    async def iniciar_evaluacion(
        self, actividad_id: UUID, estudiante_id: UUID
    ) -> tuple[Evaluacion, bool]:
        """Delega el inicio (o la reconexión idempotente) en el caso de uso correspondiente."""
        return await self._iniciar_evaluacion.execute(actividad_id, estudiante_id)

    async def registrar_respuesta(
        self,
        evaluacion_id: UUID,
        estudiante_id: UUID,
        pregunta_id: UUID,
        contenido: dict[str, Any],
    ) -> Respuesta:
        """Delega la confirmación de una respuesta en el caso de uso correspondiente."""
        return await self._registrar_respuesta.execute(
            evaluacion_id, estudiante_id, pregunta_id, contenido
        )

    async def suspender_evaluacion(self, evaluacion_id: UUID, estudiante_id: UUID) -> Evaluacion:
        """Delega la pausa explícita en el caso de uso correspondiente."""
        return await self._suspender_evaluacion.execute(evaluacion_id, estudiante_id)

    async def reanudar_evaluacion(self, evaluacion_id: UUID, estudiante_id: UUID) -> Evaluacion:
        """Delega la reanudación explícita en el caso de uso correspondiente."""
        return await self._reanudar_evaluacion.execute(evaluacion_id, estudiante_id)

    async def finalizar_evaluacion(self, evaluacion_id: UUID, estudiante_id: UUID) -> Evaluacion:
        """Delega el cierre explícito en el caso de uso correspondiente."""
        return await self._finalizar_evaluacion.execute(evaluacion_id, estudiante_id)
