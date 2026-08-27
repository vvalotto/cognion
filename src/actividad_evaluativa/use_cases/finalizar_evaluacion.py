"""Caso de uso: cierre explícito de una `Evaluacion` `EnCurso`/`Suspendida` (US-3.2.3)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.errors import EvaluacionNoExiste
from src.actividad_evaluativa.entities.evaluacion import EstadoEvaluacion, Evaluacion
from src.actividad_evaluativa.entities.eventos import EvaluacionFinalizada
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)

AGGREGATE_TYPE_EVALUACION = "Evaluacion"


class FinalizarEvaluacionUseCase:
    """Orquesta la transición `EnCurso`/`Suspendida` → `Finalizada` de una `Evaluacion`."""

    def __init__(self, event_store: EventStorePort) -> None:
        """Recibe el event store del BC."""
        self._event_store = event_store

    async def execute(self, evaluacion_id: UUID, estudiante_id: UUID) -> Evaluacion:
        """Finaliza la evaluación, o levanta el error de dominio correspondiente.

        Levanta `EvaluacionNoExiste` si `evaluacion_id` no tiene stream o no pertenece al
        estudiante autenticado, `EvaluacionYaFinalizada` si ya está `Finalizada`
        (`Evaluacion.validar_para_finalizar`). No valida período vigente — finalizar siempre
        debe poder hacerse, incluso ya vencido el período (mismo caso que dispara
        `US-3.2.4` con actor `Sistema`).
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        if not eventos:
            raise EvaluacionNoExiste(evaluacion_id)

        evaluacion = Evaluacion.reconstruir(eventos)
        if evaluacion.estudiante_id != estudiante_id:
            raise EvaluacionNoExiste(evaluacion_id)

        evaluacion.validar_para_finalizar()

        evento = EvaluacionFinalizada(evaluacion_id=evaluacion_id, actor="estudiante")
        payload = {
            "evaluacion_id": str(evento.evaluacion_id),
            "actor": evento.actor,
            "ocurrido_en": evento.ocurrido_en.isoformat(),
        }
        await self._event_store.append(
            AGGREGATE_TYPE_EVALUACION,
            evaluacion_id,
            len(eventos),
            [EventoParaAlmacenar(event_type="EvaluacionFinalizada", payload=payload)],
        )

        evaluacion.estado = EstadoEvaluacion.FINALIZADA
        return evaluacion
