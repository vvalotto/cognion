"""Caso de uso: pausa explícita de una `Evaluacion` `EnCurso` (US-3.2.2)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.errors import EvaluacionNoExiste
from src.actividad_evaluativa.entities.evaluacion import EstadoEvaluacion, Evaluacion
from src.actividad_evaluativa.entities.eventos import EvaluacionSuspendida
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)

AGGREGATE_TYPE_EVALUACION = "Evaluacion"


class SuspenderEvaluacionUseCase:
    """Orquesta la transición `EnCurso → Suspendida` de una `Evaluacion` (INV-AE-12)."""

    def __init__(self, event_store: EventStorePort) -> None:
        """Recibe el event store del BC."""
        self._event_store = event_store

    async def execute(self, evaluacion_id: UUID, estudiante_id: UUID) -> Evaluacion:
        """Suspende la evaluación, o levanta el error de dominio correspondiente.

        Levanta `EvaluacionNoExiste` si `evaluacion_id` no tiene stream o no pertenece al
        estudiante autenticado, `EvaluacionYaSuspendida`/`EvaluacionYaFinalizada` según
        INV-AE-12 (`Evaluacion.validar_para_suspender`). No valida período vigente — pausar
        siempre debe poder hacerse.
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        if not eventos:
            raise EvaluacionNoExiste(evaluacion_id)

        evaluacion = Evaluacion.reconstruir(eventos)
        if evaluacion.estudiante_id != estudiante_id:
            raise EvaluacionNoExiste(evaluacion_id)

        evaluacion.validar_para_suspender()

        evento = EvaluacionSuspendida(evaluacion_id=evaluacion_id, actor="estudiante")
        payload = {
            "evaluacion_id": str(evento.evaluacion_id),
            "actor": evento.actor,
            "ocurrido_en": evento.ocurrido_en.isoformat(),
        }
        await self._event_store.append(
            AGGREGATE_TYPE_EVALUACION,
            evaluacion_id,
            len(eventos),
            [EventoParaAlmacenar(event_type="EvaluacionSuspendida", payload=payload)],
        )

        evaluacion.estado = EstadoEvaluacion.SUSPENDIDA
        return evaluacion
