from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from src.identidad.entities.usuario import TipoPerfil
from src.identidad.frameworks.security.jwt_pyjwt import PyJWTIssuer
from src.shared.frameworks.db import SessionLocal


async def _limpiar_tablas_identidad() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM invitacion"))
        await session.execute(text("DELETE FROM comision_docentes"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM administrador"))
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


def _headers_con_rol(rol: TipoPerfil) -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid.uuid4(), rol)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


@pytest.fixture
def admin_headers() -> dict[str, str]:
    """Header `Authorization` con un JWT válido de rol `administrador` (`US-1.1.5`)."""
    return _headers_con_rol(TipoPerfil.ADMINISTRADOR)


@pytest.fixture
def docente_headers() -> dict[str, str]:
    """Header `Authorization` con un JWT válido de rol `docente` (`US-1.1.5`)."""
    return _headers_con_rol(TipoPerfil.DOCENTE)
