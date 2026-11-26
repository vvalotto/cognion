"""Gateway SQLAlchemy que implementa `EvaluacionActivaQueryPort` (US-3.2.4).

Agrupa los eventos crudos de la tabla `events` en memoria en vez de mantener una tabla de
proyección sincronizada aparte — decisión de diseño 2 de `docs/specs/inc3/US-3.2.4.md`,
confirmada con Víctor: a esta escala (30-60 alumnos) evita tocar los Use Case ya cerrados de
`US-3.1.3` a `US-3.2.3` y una migración nueva, sin riesgo de que la proyección se desincronice.
"""

from __future__ import annotations

from datetime import datetime
from itertools import groupby
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.evaluacion import EstadoEvaluacion
from src.actividad_evaluativa.entities.ports.evaluacion_activa_query_port import (
    EvaluacionActivaQueryPort,
    EvaluacionActivaResumen,
)
from src.actividad_evaluativa.frameworks.db.models import EventoModel

AGGREGATE_TYPE_EVALUACION = "Evaluacion"

_ESTADO_POR_ULTIMO_EVENTO = {
    "EvaluacionIniciada": EstadoEvaluacion.EN_CURSO,
    "RespuestaRegistrada": EstadoEvaluacion.EN_CURSO,
    "EvaluacionSuspendida": EstadoEvaluacion.SUSPENDIDA,
    "EvaluacionReanudada": EstadoEvaluacion.EN_CURSO,
    "EvaluacionFinalizada": EstadoEvaluacion.FINALIZADA,
}

_EVENT_TYPES_DE_ACTIVIDAD = {"EvaluacionIniciada", "RespuestaRegistrada", "EvaluacionReanudada"}


class SQLAlchemyEvaluacionActivaQueryRepository(EvaluacionActivaQueryPort):
    """Deriva el resumen de cada `Evaluacion` no `Finalizada` agrupando `events` en memoria."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en la consulta."""
        self._session = session

    async def listar_no_finalizadas(self) -> list[EvaluacionActivaResumen]:
        """Agrupa todos los eventos de `Evaluacion` por stream y deriva el resumen de cada uno."""
        resultado = await self._session.execute(
            select(EventoModel)
            .where(EventoModel.aggregate_type == AGGREGATE_TYPE_EVALUACION)
            .order_by(EventoModel.aggregate_id, EventoModel.sequence_number)
        )
        modelos = resultado.scalars().all()

        resumenes = []
        for _, grupo_iter in groupby(modelos, key=lambda modelo: modelo.aggregate_id):
            resumen = _resumen_de_stream(list(grupo_iter))
            if resumen.estado is not EstadoEvaluacion.FINALIZADA:
                resumenes.append(resumen)
        return resumenes


def _resumen_de_stream(eventos: list[EventoModel]) -> EvaluacionActivaResumen:
    """Deriva un `EvaluacionActivaResumen` del stream completo (ya ordenado) de una `Evaluacion`.

    Extraída a función de módulo, testeable sin sesión de BD (mismo criterio que
    `_aplicar_evento` en `entities/evaluacion.py`).
    """
    primero = eventos[0]
    return EvaluacionActivaResumen(
        evaluacion_id=primero.aggregate_id,
        actividad_id=UUID(primero.payload["actividad_id"]),
        estado=_ESTADO_POR_ULTIMO_EVENTO[eventos[-1].event_type],
        ultima_actividad_en=_ultima_actividad_en(eventos),
    )


def _ultima_actividad_en(eventos: list[EventoModel]) -> datetime:
    """`occurred_at` del evento más reciente que cuenta como actividad (`BC-...` §6, §6b)."""
    relevantes = [evento for evento in eventos if evento.event_type in _EVENT_TYPES_DE_ACTIVIDAD]
    return max(evento.occurred_at for evento in relevantes)
