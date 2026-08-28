"""Caso de uso: Docente cierra una actividad manualmente antes de tiempo (RF-11b, US-3.3.2)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import (
    ActividadEvaluativaPeriodoAbierto,
)
from src.actividad_evaluativa.entities.errors import ActividadNoExiste
from src.actividad_evaluativa.entities.eventos import ActividadEvaluativaCerrada
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.entities.ports.evaluacion_activa_query_port import (
    EvaluacionActivaQueryPort,
)
from src.actividad_evaluativa.use_cases.finalizar_evaluacion import FinalizarEvaluacionUseCase

AGGREGATE_TYPE = "ActividadEvaluativaPeriodoAbierto"


class CerrarActividadUseCase:
    """Orquesta el cierre manual (INV-AE-04b) y la cascada síncrona de finalización (Regla 3)."""

    def __init__(
        self,
        event_store: EventStorePort,
        evaluacion_activa_query: EvaluacionActivaQueryPort,
        finalizar_evaluacion: FinalizarEvaluacionUseCase,
    ) -> None:
        """Recibe el event store, el read model de evaluaciones activas y el Use Case en cascada."""
        self._event_store = event_store
        self._evaluacion_activa_query = evaluacion_activa_query
        self._finalizar_evaluacion = finalizar_evaluacion

    async def execute(self, actividad_id: UUID) -> ActividadEvaluativaPeriodoAbierto:
        """Cierra la actividad y finaliza de inmediato sus evaluaciones activas.

        Levanta `ActividadNoExiste` si `actividad_id` no tiene stream, `ActividadYaCerrada`
        (INV-AE-04b) si ya estaba cerrada manualmente. La cascada sobre cada `Evaluacion`
        `EnCurso`/`Suspendida` reutiliza `FinalizarEvaluacionUseCase` con `actor="sistema"` —
        mismo efecto que la Regla 2 del `VerificadorDeVencimientos`, disparado de inmediato en
        vez de esperar la próxima pasada del job periódico.
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE, actividad_id)
        if not eventos:
            raise ActividadNoExiste(actividad_id)

        actividad = ActividadEvaluativaPeriodoAbierto.reconstruir(eventos)
        actividad.validar_para_cerrar()

        evento = ActividadEvaluativaCerrada(actividad_id=actividad_id)
        payload = {
            "actividad_id": str(evento.actividad_id),
            "ocurrido_en": evento.ocurrido_en.isoformat(),
        }
        await self._event_store.append(
            AGGREGATE_TYPE,
            actividad_id,
            len(eventos),
            [EventoParaAlmacenar(event_type="ActividadEvaluativaCerrada", payload=payload)],
        )
        actividad.cerrada_manualmente = True

        resumen = await self._evaluacion_activa_query.listar_no_finalizadas()
        for item in resumen:
            if item.actividad_id == actividad_id:
                await self._finalizar_evaluacion.execute(item.evaluacion_id, actor="sistema")

        return actividad
