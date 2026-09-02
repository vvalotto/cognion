"""Puerto del event store append-only (`ADR-002`, `BC-actividad-evaluativa-modelo.md` §6).

Define el contrato de persistencia que cualquier aggregate de este BC usa para escribir y
reconstruir su propio stream — sin conocer SQLAlchemy ni ningún detalle de `frameworks/`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class EventoParaAlmacenar:
    """Un evento de dominio listo para persistir, previo a que se le asigne `sequence_number`."""

    event_type: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class EventoAlmacenado:
    """Un evento ya persistido, tal como lo devuelve `EventStorePort.load`."""

    sequence_number: int
    event_type: str
    payload: dict[str, Any]
    occurred_at: datetime


class EventStorePort(ABC):
    """Operaciones de append-only sobre streams `(aggregate_type, aggregate_id)`."""

    @abstractmethod
    async def append(
        self,
        aggregate_type: str,
        aggregate_id: UUID,
        expected_sequence_number: int,
        events: list[EventoParaAlmacenar],
    ) -> None:
        """Agrega `events` como los siguientes del stream, o rechaza todo el lote.

        `expected_sequence_number` es la cantidad de eventos que el llamador cree que ya
        tiene el stream (0 para un stream nuevo). Si no coincide con el último
        `sequence_number` realmente persistido, no se escribe ningún evento de `events` y se
        lanza `ConcurrenciaOptimistaError` (`entities/errors.py`). La escritura de todo el
        lote es atómica: ante cualquier falla, no queda ningún evento parcial persistido.
        """

    @abstractmethod
    async def load(self, aggregate_type: str, aggregate_id: UUID) -> list[EventoAlmacenado]:
        """Devuelve el stream completo de `(aggregate_type, aggregate_id)`, en orden.

        Lista vacía si el stream no tiene eventos todavía. Nunca incluye eventos de otro
        `aggregate_id` ni de otro `aggregate_type`.
        """
