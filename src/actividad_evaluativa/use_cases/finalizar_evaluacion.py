"""Caso de uso: cierre explícito de una `Evaluacion` `EnCurso`/`Suspendida` (US-3.2.3).

`US-3.2.4` extiende `execute()` con `actor="sistema"` para que `VerificarVencimientosUseCase`
(la Regla 2 del `VerificadorDeVencimientos`) lo reutilice sin un `estudiante_id` de contexto —
ver `BC-actividad-evaluativa-modelo.md` §6b.
"""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.errors import EvaluacionNoExiste, EvaluacionYaFinalizada
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

    async def execute(
        self,
        evaluacion_id: UUID,
        estudiante_id: UUID | None = None,
        *,
        actor: str = "estudiante",
    ) -> Evaluacion | None:
        """Finaliza la evaluación, o levanta el error de dominio correspondiente.

        Con `actor="estudiante"` (default, sin cambios de comportamiento): `estudiante_id` es
        obligatorio, se verifica pertenencia (`EvaluacionNoExiste` si no coincide), y
        `EvaluacionYaFinalizada` se propaga como feedback de UI. Con `actor="sistema"`
        (`US-3.2.4`, `VerificadorDeVencimientos`): no se verifica pertenencia y
        `EvaluacionYaFinalizada` se captura como no-op silencioso — la Policy es segura de
        re-ejecutar sobre una `Evaluacion` que ya fue finalizada por otra vía. No valida período
        vigente en ningún caso — finalizar siempre debe poder hacerse, incluso ya vencido el
        período (el caso exacto que dispara la Regla 2 con `actor="sistema"`).
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        if not eventos:
            raise EvaluacionNoExiste(evaluacion_id)

        evaluacion = Evaluacion.reconstruir(eventos)
        if actor == "estudiante" and evaluacion.estudiante_id != estudiante_id:
            raise EvaluacionNoExiste(evaluacion_id)

        try:
            evaluacion.validar_para_finalizar()
        except EvaluacionYaFinalizada:
            if actor == "sistema":
                return None
            raise

        evento = EvaluacionFinalizada(evaluacion_id=evaluacion_id, actor=actor)
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
