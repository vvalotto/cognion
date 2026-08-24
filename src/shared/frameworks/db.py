"""Motor y sesiones de SQLAlchemy async, compartidos entre BCs."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from src.settings import settings


class Base(DeclarativeBase):
    """Clase base declarativa de la que heredan todos los modelos ORM."""


# NullPool: sin conexiones asyncpg persistentes entre requests (ADR-018). Evita que una
# conexión quede atada a un event loop que ya cerró — relevante tanto para tests que corren
# en loops distintos (BDD síncrono vía asyncio.run(), pytest-asyncio por test) como para
# despliegues con múltiples workers. Costo aceptado: cada operación abre una conexión nueva.
engine = create_async_engine(settings.database_url, echo=False, poolclass=NullPool)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Provee una sesión async por request, cerrándola al finalizar."""
    async with SessionLocal() as session:
        yield session
