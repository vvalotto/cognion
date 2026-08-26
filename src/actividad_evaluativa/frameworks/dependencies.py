"""Proveedores de dependencias FastAPI (DI) del BC Actividad Evaluativa.

Composition root del BC — arranca solo con el event store (`US-3.1.1`). `US-3.1.2`/`US-3.1.3`
agregan acá sus propios use cases y controllers, mismo patrón que
`src/banco_preguntas/frameworks/dependencies.py`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.ports.event_store_port import EventStorePort
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.shared.frameworks.db import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_event_store(session: SessionDep) -> EventStorePort:
    """Provee la implementación concreta del event store del BC."""
    return SQLAlchemyEventStore(session)
