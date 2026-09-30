"""Gateway SQLAlchemy que implementa `ParticipantesSesionQueryPort` (US-6.1.3).

Deriva `participantes_por_sesion` de los eventos `EstudianteUnido` de la tabla `events` en vez de
mantener una tabla de proyección aparte — mismo criterio que
`SQLAlchemyEvaluacionActivaQueryRepository` (`US-3.2.4`): a 30-60 alumnos no justifica una
migración ni una proyección que pueda desincronizarse, y leer de los propios eventos hace la
consistencia con la escritura trivial. Reversible si el volumen cambia.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.ports.participantes_sesion_query_port import (
    ParticipanteResumen,
    ParticipantesSesionQueryPort,
)
from src.actividad_evaluativa.frameworks.db.models import EventoModel

AGGREGATE_TYPE_PARTICIPACION = "ParticipacionEnVivo"


class SQLAlchemyParticipantesSesionQueryRepository(ParticipantesSesionQueryPort):
    """Lista los `EstudianteUnido` de una sesión, filtrando por `payload->>'sesion_id'`."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en la consulta."""
        self._session = session

    async def listar(self, sesion_id: UUID) -> list[ParticipanteResumen]:
        """Devuelve los participantes de la sesión en orden de unión (más antiguo primero)."""
        resultado = await self._session.execute(
            select(EventoModel)
            .where(
                EventoModel.aggregate_type == AGGREGATE_TYPE_PARTICIPACION,
                EventoModel.event_type == "EstudianteUnido",
                EventoModel.payload["sesion_id"].astext == str(sesion_id),
            )
            .order_by(EventoModel.occurred_at, EventoModel.aggregate_id)
        )
        return [
            ParticipanteResumen(
                estudiante_id=UUID(modelo.payload["estudiante_id"]),
                unido_en=datetime.fromisoformat(modelo.payload["unido_en"]),
            )
            for modelo in resultado.scalars().all()
        ]
