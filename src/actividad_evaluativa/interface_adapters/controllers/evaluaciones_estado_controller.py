"""Controller de la API para suspender, reanudar y finalizar una evaluación (INV-AE-12)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort
from src.actividad_evaluativa.interface_adapters.controllers._contenido_de_evaluacion import (
    contenidos_de,
)
from src.actividad_evaluativa.interface_adapters.presenters.evaluacion_presenter import (
    EvaluacionSalida,
    presentar_evaluacion,
)
from src.actividad_evaluativa.use_cases.finalizar_evaluacion import FinalizarEvaluacionUseCase
from src.actividad_evaluativa.use_cases.reanudar_evaluacion import ReanudarEvaluacionUseCase
from src.actividad_evaluativa.use_cases.suspender_evaluacion import SuspenderEvaluacionUseCase


class EvaluacionesEstadoController:
    """Adapta requests HTTP a las transiciones de estado de una evaluación."""

    def __init__(
        self,
        suspender_evaluacion: SuspenderEvaluacionUseCase,
        reanudar_evaluacion: ReanudarEvaluacionUseCase,
        finalizar_evaluacion: FinalizarEvaluacionUseCase,
        pregunta_consulta: PreguntaConsultaPort,
    ) -> None:
        """Recibe los casos de uso y el puerto que enriquece la evaluación con sus preguntas."""
        self._suspender_evaluacion = suspender_evaluacion
        self._reanudar_evaluacion = reanudar_evaluacion
        self._finalizar_evaluacion = finalizar_evaluacion
        self._pregunta_consulta = pregunta_consulta

    async def suspender_evaluacion(
        self, evaluacion_id: UUID, estudiante_id: UUID
    ) -> EvaluacionSalida:
        """Suspende la evaluación del Estudiante y la presenta."""
        evaluacion = await self._suspender_evaluacion.execute(evaluacion_id, estudiante_id)
        return presentar_evaluacion(
            evaluacion, await contenidos_de(evaluacion, self._pregunta_consulta)
        )

    async def reanudar_evaluacion(
        self, evaluacion_id: UUID, estudiante_id: UUID
    ) -> EvaluacionSalida:
        """Reanuda la evaluación suspendida del Estudiante y la presenta."""
        evaluacion = await self._reanudar_evaluacion.execute(evaluacion_id, estudiante_id)
        return presentar_evaluacion(
            evaluacion, await contenidos_de(evaluacion, self._pregunta_consulta)
        )

    async def finalizar_evaluacion(
        self, evaluacion_id: UUID, estudiante_id: UUID
    ) -> EvaluacionSalida:
        """Finaliza la evaluación del Estudiante y la presenta."""
        evaluacion = await self._finalizar_evaluacion.execute(evaluacion_id, estudiante_id)
        return presentar_evaluacion(
            evaluacion, await contenidos_de(evaluacion, self._pregunta_consulta)
        )
