"""Controller de la API para operaciones sobre evaluaciones de un Estudiante."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.evaluacion import Evaluacion
from src.actividad_evaluativa.use_cases.iniciar_evaluacion import IniciarEvaluacionUseCase


class EvaluacionesController:
    """Adapta requests HTTP al caso de uso de inicio de evaluaciones."""

    def __init__(self, iniciar_evaluacion: IniciarEvaluacionUseCase) -> None:
        """Recibe el caso de uso de inicio de evaluaciones."""
        self._iniciar_evaluacion = iniciar_evaluacion

    async def iniciar_evaluacion(
        self, actividad_id: UUID, estudiante_id: UUID
    ) -> tuple[Evaluacion, bool]:
        """Delega el inicio (o la reconexión idempotente) en el caso de uso correspondiente."""
        return await self._iniciar_evaluacion.execute(actividad_id, estudiante_id)
