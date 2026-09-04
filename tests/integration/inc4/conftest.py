from __future__ import annotations

import pytest
from sqlalchemy import text

from src.shared.frameworks.db import SessionLocal


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.commit()


@pytest.fixture(autouse=True)
async def limpiar_tablas_analytics():
    await _limpiar_tablas()
    yield
    await _limpiar_tablas()
