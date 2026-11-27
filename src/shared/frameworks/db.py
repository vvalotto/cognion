"""Motor y sesiones de SQLAlchemy async, compartidos entre BCs."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from starlette.exceptions import HTTPException

from src.settings import Settings, settings


class Base(DeclarativeBase):
    """Clase base declarativa de la que heredan todos los modelos ORM."""


def crear_motor(config: Settings) -> AsyncEngine:
    """Arma el motor según la configuración (`ADR-018`, enmendado en `US-12.2.5`).

    En ejecución usa un pool de conexiones con `pool_pre_ping`: una sesión en vivo con 60 alumnos
    reutiliza conexiones en vez de abrir una por operación. Con `db_pool="nula"` usa `NullPool`, sin
    conexiones persistentes: lo piden los tests, porque cada paso del BDD (`asyncio.run()`) y cada test de
    `pytest-asyncio` corre en un event loop distinto y una conexión de `asyncpg` queda atada al loop que la creó.
    El pool vale mientras haya un solo proceso y un solo loop (`docs/INSTALACION.md`).
    """
    if config.db_pool == "nula":
        return create_async_engine(config.database_url, echo=False, poolclass=NullPool)
    return create_async_engine(
        config.database_url,
        echo=False,
        pool_size=config.db_pool_size,
        max_overflow=config.db_max_overflow,
        pool_timeout=config.db_pool_timeout,
        pool_pre_ping=True,
    )


engine = crear_motor(settings)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


def es_error_controlado(exc: BaseException) -> bool:
    """Dice si `exc` es el resultado de una regla de negocio o de un control de seguridad.

    Un error controlado es una respuesta esperada y se respeta: lo escrito hasta ese punto
    se confirma (por ejemplo, el intento fallido de login que cuenta para el bloqueo de
    cuenta, `INV-ID-21`). Lo son un `HTTPException` con código menor a 500 y toda clase
    definida en un `entities/errors.py`, que se reconoce por el módulo donde está para no
    importar ningún contexto. Cualquier otra excepción es una falla técnica (acceso a la
    base, pérdida de la conexión, un error del código) y revierte todo (`ADR-028`, enmienda
    del 2026-11-26).
    """
    if isinstance(exc, HTTPException):
        return exc.status_code < 500
    return type(exc).__module__.endswith(".entities.errors")


@asynccontextmanager
async def unidad_de_trabajo() -> AsyncIterator[AsyncSession]:
    """Abre una sesión; la confirma al salir bien o ante un error controlado, si no la revierte.

    Es la única unidad de trabajo del proyecto: la usan `get_session` (un request) y los
    puntos de entrada que no lo son (CLI, tests). Los repositorios hacen `flush()` y no
    confirman. El event store de Actividad Evaluativa sigue confirmando en `append`
    (`ADR-028`). Si la tarea se cancela, el cierre de la sesión descarta lo pendiente.
    """
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as exc:
            if es_error_controlado(exc):
                await session.commit()
            else:
                await session.rollback()
            raise
        await session.commit()


async def get_session() -> AsyncIterator[AsyncSession]:
    """Provee una sesión por request y la confirma o revierte al terminar (`unidad_de_trabajo`)."""
    async with unidad_de_trabajo() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session, scope="function")]
"""Sesión del request.

`scope="function"` es obligatorio: con el alcance por defecto, un `commit()` que falla después
del `yield` ocurre cuando el cliente ya recibió el 200 (FastAPI 0.139, `ADR-028`).
"""
