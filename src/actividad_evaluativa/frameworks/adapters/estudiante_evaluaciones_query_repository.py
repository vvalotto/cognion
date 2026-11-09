"""Gateway SQLAlchemy que implementa `EstudianteEvaluacionesQueryPort` (`US-9.4.3`)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.ports.estudiante_evaluaciones_query_port import (
    EstudianteEvaluacionesQueryPort,
)
from src.actividad_evaluativa.frameworks.db.models import EventoModel

AGGREGATE_TYPE_EVALUACION = "Evaluacion"
EVENT_TYPE_INICIADA = "EvaluacionIniciada"


class SQLAlchemyEstudianteEvaluacionesQueryRepository(EstudianteEvaluacionesQueryPort):
    """Busca eventos `EvaluacionIniciada` del estudiante en el event store.

    Filtra el `payload` en memoria (sin operadores JSONB), por consistencia con el resto del
    proyecto.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async compartida con el event store."""
        self._session = session

    async def tiene_evaluaciones_iniciadas(self, estudiante_id: UUID) -> bool:
        """Indica si el estudiante inició alguna vez una evaluación (cualquier estado)."""
        query = select(EventoModel.payload).where(
            EventoModel.aggregate_type == AGGREGATE_TYPE_EVALUACION,
            EventoModel.event_type == EVENT_TYPE_INICIADA,
        )
        resultado = await self._session.execute(query)
        estudiante_id_str = str(estudiante_id)
        return any(payload["estudiante_id"] == estudiante_id_str for payload in resultado.scalars())
