"""Caso de uso: pausa explícita de una `Evaluacion` `EnCurso` (US-3.2.2).

`US-3.2.4` extiende `execute()` con `actor="sistema"` para que `VerificarVencimientosUseCase`
(la Regla 1 del `VerificadorDeVencimientos`) lo reutilice sin un `estudiante_id` de contexto —
ver `BC-actividad-evaluativa-modelo.md` §6b.
"""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.errors import (
    EvaluacionNoExiste,
    EvaluacionYaFinalizada,
    EvaluacionYaSuspendida,
)
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

    async def execute(
        self,
        evaluacion_id: UUID,
        estudiante_id: UUID | None = None,
        *,
        actor: str = "estudiante",
    ) -> Evaluacion | None:
        """Suspende la evaluación, o levanta el error de dominio correspondiente.

        Con `actor="estudiante"` (default, sin cambios de comportamiento): `estudiante_id` es
        obligatorio, se verifica pertenencia (`EvaluacionNoExiste` si no coincide), y
        `EvaluacionYaSuspendida`/`EvaluacionYaFinalizada` (INV-AE-12) se propagan como feedback
        de UI. Con `actor="sistema"` (`US-3.2.4`, `VerificadorDeVencimientos`): no se verifica
        pertenencia (la Policy ya seleccionó `evaluacion_id` desde el read model, sin usuario a
        impersonar) y esos mismos errores se capturan como no-op silencioso — la Policy es
        segura de re-ejecutar sobre una `Evaluacion` que ya cambió de estado por otra vía.
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        if not eventos:
            raise EvaluacionNoExiste(evaluacion_id)

        evaluacion = Evaluacion.reconstruir(eventos)
        if actor == "estudiante" and evaluacion.estudiante_id != estudiante_id:
            raise EvaluacionNoExiste(evaluacion_id)

        try:
            evaluacion.validar_para_suspender()
        except (EvaluacionYaSuspendida, EvaluacionYaFinalizada):
            if actor == "sistema":
                return None
            raise

        evento = EvaluacionSuspendida(evaluacion_id=evaluacion_id, actor=actor)
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
