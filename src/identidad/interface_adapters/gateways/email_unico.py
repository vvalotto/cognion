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
    """Convierte la violación de unicidad del email en `EmailYaRegistrado` y deshace la sesión.

    Dos registros del mismo email a la vez pasan juntos el chequeo previo `existe_email` y los
    frena la restricción única: es el mismo "email ya registrado", no un error 500. Cualquier otra
    violación de integridad se vuelve a lanzar tal cual.
    """
    try:
        yield
    except IntegrityError as exc:
        await session.rollback()
        if _RESTRICCION_EMAIL in str(exc):
            raise EmailYaRegistrado(email) from exc
        raise
