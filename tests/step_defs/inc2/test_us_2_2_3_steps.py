from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc1._auth_headers import admin_headers

scenarios("../../features/inc2/US-2.2.3-detalle-cuenta.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


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
def limpiar_tablas_identidad():
    run_async(_limpiar_tablas_identidad())
    yield
    run_async(_limpiar_tablas_identidad())


@pytest.fixture
def context():
    return {}


async def _get(path: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path, headers=admin_headers())


async def _crear_docente() -> uuid.UUID:
    hasher = BcryptPasswordHasher()
    async with SessionLocal() as session:
        repo = SQLAlchemyUsuarioRepository(session)
        email = f"docente.bdd223.{uuid.uuid4()}@fiuner.edu.ar"
        usuario = Usuario.crear("Docente BDD", email, hasher.hash("x"), TipoPerfil.DOCENTE)
        await repo.guardar(usuario)
        return usuario.id


async def _crear_estudiante() -> tuple[uuid.UUID, uuid.UUID]:
    hasher = BcryptPasswordHasher()
    async with SessionLocal() as session:
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear(
            "Admin BDD Comision",
            f"admin.bdd223.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("x"),
            TipoPerfil.ADMINISTRADOR,
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        estudiante = Usuario.crear_estudiante(
            "Estudiante BDD",
            f"estudiante.bdd223.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("x"),
            comision.id,
        )
        await usuario_repo.guardar(estudiante)
        return estudiante.id, comision.id


@given("un Usuario con perfil Estudiante asignado a una Comisión")
def usuario_estudiante_con_comision(context):
    usuario_id, comision_id = run_async(_crear_estudiante())
    context["usuario_id"] = usuario_id
    context["comision_id"] = comision_id


@given("un Usuario con perfil Docente")
def usuario_docente(context):
    context["usuario_id"] = run_async(_crear_docente())


@given("ningún Usuario tiene el id provisto")
def ningun_usuario_con_el_id(context):
    context["usuario_id"] = uuid.uuid4()


@when(parsers.parse("un Administrador ejecuta ObtenerCuenta(usuario_id)"))
def ejecuta_obtener_cuenta(context):
    context["response"] = run_async(_get(f"/usuarios/{context['usuario_id']}"))


@then("el sistema devuelve sus datos incluyendo comision_id")
def valida_devuelve_datos_con_comision_id(context):
    assert context["response"].status_code == 200
    body = context["response"].json()
    assert body["comision_id"] == str(context["comision_id"])


@then("el sistema devuelve sus datos con comision_id en null")
def valida_devuelve_datos_con_comision_id_null(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["comision_id"] is None


@then("el sistema rechaza con UsuarioNoExiste")
def valida_rechazo_usuario_no_existe(context):
    assert context["response"].status_code == 404
