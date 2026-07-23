from __future__ import annotations

import pytest
from sqlalchemy import text

from src.shared.frameworks.db import SessionLocal


async def _limpiar_tablas_identidad() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM invitacion"))
        await session.execute(text("DELETE FROM comision_docentes"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM usuario"))
        await session.commit()


@pytest.fixture(autouse=True)
async def limpiar_tablas_identidad():
    await _limpiar_tablas_identidad()
    yield
    await _limpiar_tablas_identidad()


@pytest.fixture
async def session():
    async with SessionLocal() as session:
        yield session
