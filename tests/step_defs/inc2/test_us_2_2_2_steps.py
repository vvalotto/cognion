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

scenarios("../../features/inc2/US-2.2.2-listado-cuentas.feature")


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


async def _crear_cuenta(
    nombre: str, email: str, tipo_perfil: TipoPerfil, bloqueada: bool = False
) -> None:
    hasher = BcryptPasswordHasher()
    async with SessionLocal() as session:
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        if tipo_perfil is TipoPerfil.ESTUDIANTE:
            comision_repo = SQLAlchemyComisionRepository(session)
            admin = Usuario.crear(
                "Admin BDD Comision",
                f"admin.bdd222.{uuid.uuid4()}@fiuner.edu.ar",
                hasher.hash("x"),
                TipoPerfil.ADMINISTRADOR,
            )
            await usuario_repo.guardar(admin)
            comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
            await comision_repo.guardar(comision)
            usuario = Usuario.crear_estudiante(
                nombre, email, hasher.hash("Correcta#2026"), comision.id
            )
        else:
            usuario = Usuario.crear(nombre, email, hasher.hash("Correcta#2026"), tipo_perfil)
        await usuario_repo.guardar(usuario)
        if bloqueada:
            usuario.bloqueada = True
            await usuario_repo.actualizar(usuario)


async def _get(path: str, params: dict | None = None):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path, params=params, headers=admin_headers())


@given("existen cuentas de distintos roles y estados")
def cuentas_de_distintos_roles_y_estados(context):
    run_async(
        _crear_cuenta("Docente BDD", "docente.bdd222@fiuner.edu.ar", TipoPerfil.DOCENTE)
    )
    run_async(
        _crear_cuenta(
            "Admin BDD", "admin.bdd222@fiuner.edu.ar", TipoPerfil.ADMINISTRADOR, bloqueada=True
        )
    )


@given("existen Estudiantes activos y bloqueados, y Docentes activos")
def estudiantes_y_docentes_variados(context):
    run_async(
        _crear_cuenta(
            "Estudiante Activo", "est.activo.bdd222@fiuner.edu.ar", TipoPerfil.ESTUDIANTE
        )
    )
    run_async(
        _crear_cuenta(
            "Estudiante Bloqueado",
            "est.bloqueado.bdd222@fiuner.edu.ar",
            TipoPerfil.ESTUDIANTE,
            bloqueada=True,
        )
    )
    run_async(
        _crear_cuenta("Docente Activo", "docente.activo.bdd222@fiuner.edu.ar", TipoPerfil.DOCENTE)
    )


@given(parsers.parse('existe una cuenta con email "{email}"'))
def existe_cuenta_con_email(context, email):
    run_async(_crear_cuenta("Docente Buscado", email, TipoPerfil.DOCENTE))
    context["email_buscado"] = email


@when("un Administrador ejecuta ListarCuentas() sin filtros")
def ejecuta_listar_cuentas_sin_filtros(context):
    context["response"] = run_async(_get("/usuarios"))


@when("un Administrador ejecuta ListarCuentas(rol=estudiante, estado=bloqueada)")
def ejecuta_listar_cuentas_rol_estudiante_bloqueada(context):
    context["response"] = run_async(
        _get("/usuarios", params={"rol": "estudiante", "estado": "bloqueada"})
    )


@when(parsers.parse('un Administrador ejecuta ListarCuentas(busqueda="{busqueda}")'))
def ejecuta_listar_cuentas_busqueda(context, busqueda):
    context["response"] = run_async(_get("/usuarios", params={"busqueda": busqueda}))


@then("el sistema devuelve todas las cuentas")
def valida_devuelve_todas_las_cuentas(context):
    assert context["response"].status_code == 200
    assert len(context["response"].json()) >= 2


@then("el sistema devuelve solo los Estudiantes con bloqueada = true")
def valida_devuelve_solo_estudiantes_bloqueados(context):
    assert context["response"].status_code == 200
    cuentas = context["response"].json()
    assert len(cuentas) == 1
    assert cuentas[0]["perfil"] == "estudiante"
    assert cuentas[0]["bloqueada"] is True


@then("esa cuenta aparece en el resultado")
def valida_cuenta_aparece_en_resultado(context):
    assert context["response"].status_code == 200
    emails = [c["email"] for c in context["response"].json()]
    assert context["email_buscado"] in emails
