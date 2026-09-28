from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Docente, Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer


async def _limpiar_tablas_identidad() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM token_recuperacion_password"))
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


def _id_desde_headers(headers: dict[str, str]) -> uuid.UUID:
    """Extrae el `usuario_id` codificado en un header `Authorization: Bearer <jwt>`."""
    token = headers["Authorization"].removeprefix("Bearer ")
    return PyJWTIssuer().verificar(token).usuario_id


async def asignar_docente_a_materia(materia_id: str, docente_headers: dict[str, str]) -> None:
    """Crea la fila real del Docente de `docente_headers` y una Comisión de `materia_id` asignada.

    `US-ADJ-57`: `POST /preguntas/*` exige que el Docente que llama tenga una Comisión asignada
    en la materia del banco — `docente_headers` (fixture de este conftest) es un JWT anónimo sin
    fila `Usuario`, insuficiente por sí solo. Este helper materializa esa fila con el mismo id
    del JWT (para no invalidarlo) y la asigna, sin que los helpers de carga de cada test tengan
    que cambiar de identidad ni los tests pedir un fixture nuevo.
    """
    docente_id = _id_desde_headers(docente_headers)
    async with SessionLocal() as session:
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)

        admin = Usuario.crear(
            "Admin",
            f"admin.{uuid.uuid4()}@fiuner.edu.ar",
            BcryptPasswordHasher().hash("x"),
            TipoPerfil.ADMINISTRADOR,
        )
        await usuario_repo.guardar(admin)
        docente = Usuario(
            id=docente_id,
            nombre="Docente",
            email=f"docente.{uuid.uuid4()}@fiuner.edu.ar",
            password_hash=BcryptPasswordHasher().hash("x"),
            perfil=Docente(id=docente_id),
        )
        await usuario_repo.guardar(docente)

        comision = Comision.crear(uuid.UUID(materia_id), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        comision.asignar_docente(docente_id)
        await comision_repo.actualizar(comision)
