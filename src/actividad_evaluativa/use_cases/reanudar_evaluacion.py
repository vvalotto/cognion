"""Caso de uso: reanudación explícita de una `Evaluacion` `Suspendida` (US-3.2.2)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from src.actividad_evaluativa.entities.errors import EvaluacionNoExiste, FueraDePeriodo
from src.actividad_evaluativa.entities.evaluacion import EstadoEvaluacion, Evaluacion
from src.actividad_evaluativa.entities.eventos import EvaluacionReanudada
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)

AGGREGATE_TYPE_ACTIVIDAD = "ActividadEvaluativaPeriodoAbierto"
AGGREGATE_TYPE_EVALUACION = "Evaluacion"


class ReanudarEvaluacionUseCase:
    """Orquesta la transición `Suspendida → EnCurso` de una `Evaluacion` (INV-AE-11)."""

    def __init__(self, event_store: EventStorePort) -> None:
        """Recibe el event store del BC."""
        self._event_store = event_store

    async def execute(self, evaluacion_id: UUID, estudiante_id: UUID) -> Evaluacion:
        """Reanuda la evaluación, o levanta el error de dominio correspondiente.

        Levanta `EvaluacionNoExiste` si `evaluacion_id` no tiene stream o no pertenece al
        estudiante autenticado, `EvaluacionNoSuspendida`/`EvaluacionYaFinalizada` según
        INV-AE-11 (`Evaluacion.validar_para_reanudar`), `FueraDePeriodo` si la actividad ya no
        está dentro de su ventana vigente.
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        if not eventos:
            raise EvaluacionNoExiste(evaluacion_id)

        evaluacion = Evaluacion.reconstruir(eventos)
        if evaluacion.estudiante_id != estudiante_id:
            raise EvaluacionNoExiste(evaluacion_id)

        evaluacion.validar_para_reanudar()

        eventos_actividad = await self._event_store.load(
            AGGREGATE_TYPE_ACTIVIDAD, evaluacion.actividad_id
        )
        actividad = eventos_actividad[0].payload
        fecha_apertura = datetime.fromisoformat(actividad["fecha_apertura"])
        fecha_cierre = datetime.fromisoformat(actividad["fecha_cierre"])

        ahora = datetime.now(UTC)
        if ahora < fecha_apertura or ahora > fecha_cierre:
            raise FueraDePeriodo(evaluacion.actividad_id, ahora)

        evento = EvaluacionReanudada(evaluacion_id=evaluacion_id)
        payload = {
            "evaluacion_id": str(evento.evaluacion_id),
            "ocurrido_en": evento.ocurrido_en.isoformat(),
        }
        await self._event_store.append(
            AGGREGATE_TYPE_EVALUACION,
            evaluacion_id,
            len(eventos),
            [EventoParaAlmacenar(event_type="EvaluacionReanudada", payload=payload)],
        )

        evaluacion.estado = EstadoEvaluacion.EN_CURSO
        return evaluacion
