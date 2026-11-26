"""Gateway SQLAlchemy que implementa `EvaluacionEstudianteQueryPort` (`US-3.4.5`)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.ports.evaluacion_estudiante_query_port import (
    EvaluacionEstudianteQueryPort,
)
from src.actividad_evaluativa.frameworks.db.models import EventoModel

AGGREGATE_TYPE_EVALUACION = "Evaluacion"
EVENT_TYPE_FINALIZADA = "EvaluacionFinalizada"


class SQLAlchemyEvaluacionEstudianteQueryRepository(EvaluacionEstudianteQueryPort):
    """Verifica la existencia del evento terminal `EvaluacionFinalizada`, sin replay completo."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en la consulta."""
        self._session = session

    async def existentes_finalizadas(self, evaluacion_ids: list[UUID]) -> set[UUID]:
        """Devuelve el subconjunto de `evaluacion_ids` con un evento `EvaluacionFinalizada`."""
        if not evaluacion_ids:
            return set()
        resultado = await self._session.execute(
            select(EventoModel.aggregate_id)
            .where(
                EventoModel.aggregate_type == AGGREGATE_TYPE_EVALUACION,
                EventoModel.aggregate_id.in_(evaluacion_ids),
                EventoModel.event_type == EVENT_TYPE_FINALIZADA,
            )
            .distinct()
        )
        return set(resultado.scalars().all())
