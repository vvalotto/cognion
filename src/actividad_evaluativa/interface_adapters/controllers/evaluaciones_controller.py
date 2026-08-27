"""Controller de la API para operaciones sobre evaluaciones de un Estudiante."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.evaluacion import Evaluacion, Respuesta
from src.actividad_evaluativa.use_cases.iniciar_evaluacion import IniciarEvaluacionUseCase
from src.actividad_evaluativa.use_cases.registrar_respuesta import RegistrarRespuestaUseCase


class EvaluacionesController:
    """Adapta requests HTTP a los casos de uso sobre evaluaciones de un Estudiante."""

    def __init__(
        self,
        iniciar_evaluacion: IniciarEvaluacionUseCase,
        registrar_respuesta: RegistrarRespuestaUseCase,
    ) -> None:
        """Recibe los casos de uso de inicio de evaluaciones y registro de respuestas."""
        self._iniciar_evaluacion = iniciar_evaluacion
        self._registrar_respuesta = registrar_respuesta

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
