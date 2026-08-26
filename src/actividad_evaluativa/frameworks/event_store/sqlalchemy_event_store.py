"""Gateway SQLAlchemy que implementa `EventStorePort`."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.errors import ConcurrenciaOptimistaError
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoAlmacenado,
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.frameworks.db.models import EventoModel


class SQLAlchemyEventStore(EventStorePort):
    """Persiste y reproduce streams de eventos usando SQLAlchemy async.

    `append` valida `expected_sequence_number` contra el último `sequence_number` realmente
    persistido antes de insertar — mismo criterio de "leer antes de escribir dentro de la
    propia transacción" que el resto de los repositorios del proyecto (ej.
    `SQLAlchemyMateriaRepository.guardar`, que verifica unicidad de nombre antes del insert).
    El índice único de `EventoModel` (`uq_events_stream_sequence`) queda como respaldo ante
    una escritura concurrente genuina entre dos transacciones distintas.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en las operaciones."""
        self._session = session

    async def append(
        self,
        aggregate_type: str,
        aggregate_id: UUID,
        expected_sequence_number: int,
        events: list[EventoParaAlmacenar],
    ) -> None:
        """Inserta `events` como los siguientes del stream, o rechaza el lote completo."""
        ultimo_sequence_number = await self._ultimo_sequence_number(
            aggregate_type, aggregate_id
        )
        if ultimo_sequence_number != expected_sequence_number:
            raise ConcurrenciaOptimistaError(
                aggregate_type, aggregate_id, expected_sequence_number, ultimo_sequence_number
            )

        ahora = datetime.now(UTC)
        for indice, evento in enumerate(events, start=1):
            self._session.add(
                EventoModel(
                    aggregate_type=aggregate_type,
                    aggregate_id=aggregate_id,
                    sequence_number=expected_sequence_number + indice,
                    event_type=evento.event_type,
                    payload=evento.payload,
                    occurred_at=ahora,
                )
            )
        await self._session.commit()

    async def load(self, aggregate_type: str, aggregate_id: UUID) -> list[EventoAlmacenado]:
        """Devuelve el stream completo de `(aggregate_type, aggregate_id)`, en orden."""
        resultado = await self._session.execute(
            select(EventoModel)
            .where(
                EventoModel.aggregate_type == aggregate_type,
                EventoModel.aggregate_id == aggregate_id,
            )
            .order_by(EventoModel.sequence_number)
        )
        return [
            EventoAlmacenado(
                sequence_number=modelo.sequence_number,
                event_type=modelo.event_type,
                payload=modelo.payload,
                occurred_at=modelo.occurred_at,
            )
            for modelo in resultado.scalars()
        ]

    async def _ultimo_sequence_number(self, aggregate_type: str, aggregate_id: UUID) -> int:
        """Último `sequence_number` persistido del stream, o `0` si está vacío."""
        resultado = await self._session.execute(
            select(func.max(EventoModel.sequence_number)).where(
                EventoModel.aggregate_type == aggregate_type,
                EventoModel.aggregate_id == aggregate_id,
            )
        )
        return resultado.scalar_one_or_none() or 0
