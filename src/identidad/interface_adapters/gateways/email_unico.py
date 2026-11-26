"""Traducción de la violación de la restricción única del email a `EmailYaRegistrado` (`US-ADJ-67`)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.identidad.entities.errors import EmailYaRegistrado

_RESTRICCION_EMAIL = "usuario_email_key"


@asynccontextmanager
async def email_unico(session: AsyncSession, email: str) -> AsyncIterator[None]:
    """Convierte la violación de unicidad del email en `EmailYaRegistrado`, deshaciendo solo lo de este bloque.

    Dos registros del mismo email a la vez pasan juntos el chequeo previo `existe_email` y los
    frena la restricción única: es el mismo "email ya registrado", no un error 500. Cualquier otra
    violación de integridad se vuelve a lanzar tal cual.

    El bloque corre dentro de un punto de guardado (`begin_nested`) y no deshace la sesión entera: con
    la unidad de trabajo por request (`ADR-028`), un `rollback()` de la sesión descartaría también lo que
    el request ya había escrito antes. El `flush()` que dispara la violación debe estar dentro del bloque.
    """
    try:
        async with session.begin_nested():
            yield
    except IntegrityError as exc:
        if _RESTRICCION_EMAIL in str(exc):
            raise EmailYaRegistrado(email) from exc
        raise
