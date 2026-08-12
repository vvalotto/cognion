from __future__ import annotations

import pytest
from sqlalchemy import text

from src.shared.frameworks.db import SessionLocal


async def _limpiar_tablas_banco_preguntas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.commit()


@pytest.fixture(autouse=True)
async def limpiar_tablas_banco_preguntas():
    await _limpiar_tablas_banco_preguntas()
    yield
    await _limpiar_tablas_banco_preguntas()
