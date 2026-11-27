"""Controller de la API para iniciar una evaluación y registrar respuestas.

Las transiciones de estado (suspender, reanudar, finalizar) están en `EvaluacionesEstadoController`:
al presentar la evaluación, ambos controllers necesitan `PreguntaConsultaPort` y juntos pasaban el
umbral de CBO (`IQ-01`).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort
from src.actividad_evaluativa.interface_adapters.controllers._contenido_de_evaluacion import (
    contenidos_de,
)
from src.actividad_evaluativa.interface_adapters.presenters.evaluacion_presenter import (
    EvaluacionSalida,
    RespuestaSalida,
    presentar_evaluacion,
    presentar_respuesta,
)
from src.actividad_evaluativa.use_cases.iniciar_evaluacion import IniciarEvaluacionUseCase
from src.actividad_evaluativa.use_cases.registrar_respuesta import RegistrarRespuestaUseCase


class EvaluacionesController:
    """Adapta requests HTTP a los casos de uso de inicio y respuesta de una evaluación."""

    def __init__(
        self,
        iniciar_evaluacion: IniciarEvaluacionUseCase,
        registrar_respuesta: RegistrarRespuestaUseCase,
        pregunta_consulta: PreguntaConsultaPort,
    ) -> None:
        """Recibe los casos de uso y el puerto que enriquece la evaluación con sus preguntas."""
        self._iniciar_evaluacion = iniciar_evaluacion
        self._registrar_respuesta = registrar_respuesta
        self._pregunta_consulta = pregunta_consulta

    async def iniciar_evaluacion(self, actividad_id: UUID, estudiante_id: UUID) -> EvaluacionSalida:
        """Inicia (o retoma, idempotente) la evaluación y la presenta con el contenido de sus preguntas."""
        evaluacion, _creada = await self._iniciar_evaluacion.execute(actividad_id, estudiante_id)
        contenidos = await contenidos_de(evaluacion, self._pregunta_consulta)
        return presentar_evaluacion(evaluacion, contenidos)

    async def registrar_respuesta(
        self, evaluacion_id: UUID, estudiante_id: UUID, pregunta_id: UUID, contenido: dict[str, Any]
    ) -> RespuestaSalida:
        """Registra la respuesta del Estudiante y la presenta (sin `es_correcta`)."""
        respuesta = await self._registrar_respuesta.execute(
            evaluacion_id, estudiante_id, pregunta_id, contenido
        )
        return presentar_respuesta(respuesta)
