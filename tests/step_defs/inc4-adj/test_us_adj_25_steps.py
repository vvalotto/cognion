"""Steps BDD de US-ADJ-25 (`tests/features/inc4-adj/US-ADJ-25-asignar-docente-comision.feature`)."""

from __future__ import annotations

import asyncio
import uuid
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer

scenarios("../../features/inc4-adj/US-ADJ-25-asignar-docente-comision.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision_docentes"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM usuario"))
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {}


def _headers(perfil: TipoPerfil) -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid4(), perfil)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


def _headers_docente() -> dict[str, str]:
    return _headers(TipoPerfil.DOCENTE)


def _headers_administrador() -> dict[str, str]:
    return _headers(TipoPerfil.ADMINISTRADOR)


def _headers_estudiante() -> dict[str, str]:
    return _headers(TipoPerfil.ESTUDIANTE)


async def _crear_admin(session) -> Usuario:
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    return admin


async def _crear_comision(con_docente: bool) -> tuple[Comision, Usuario | None]:
    async with SessionLocal() as session:
        admin = await _crear_admin(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        docente = None
        if con_docente:
            usuario_repo = SQLAlchemyUsuarioRepository(session)
            docente = Usuario.crear(
                "Docente", f"docente.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE
            )
            await usuario_repo.guardar(docente)
            comision.asignar_docente(docente.id)
            await comision_repo.actualizar(comision)

        return comision, docente


async def _crear_usuario(perfil: TipoPerfil) -> Usuario:
    async with SessionLocal() as session:
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        if perfil == TipoPerfil.ESTUDIANTE:
            comision, _ = await _crear_comision(con_docente=False)
            usuario = Usuario.crear_estudiante(
                "Estudiante", f"est.{uuid.uuid4()}@fiuner.edu.ar", "hash", comision.id
            )
        else:
            usuario = Usuario.crear("Usuario", f"usr.{uuid.uuid4()}@fiuner.edu.ar", "hash", perfil)
        await usuario_repo.guardar(usuario)
        return usuario


def _get(context, path: str, headers) -> None:
    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(path, headers=headers)

    context["response"] = run_async(_call())


def _post(context, path: str, body: dict, headers) -> None:
    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(path, json=body, headers=headers)

    context["response"] = run_async(_call())


@given("una comisión sin ningún docente asignado")
def comision_sin_docente(context):
    comision, _ = run_async(_crear_comision(con_docente=False))
    context["comision"] = comision


@given("una comisión con un docente asignado")
def comision_con_docente(context):
    comision, docente = run_async(_crear_comision(con_docente=True))
    context["comision"] = comision
    context["docente"] = docente


@given("un usuario con perfil Docente")
def usuario_docente(context):
    context["usuario"] = run_async(_crear_usuario(TipoPerfil.DOCENTE))


@given("un usuario con perfil Estudiante")
def usuario_estudiante(context):
    context["usuario"] = run_async(_crear_usuario(TipoPerfil.ESTUDIANTE))


@given("un id de comisión que no existe")
def id_de_comision_inexistente(context):
    context["comision_id"] = uuid4()


@given("un Estudiante autenticado")
def estudiante_autenticado(context):
    comision, _ = run_async(_crear_comision(con_docente=True))
    context["comision"] = comision


@when("un Administrador hace GET /comisiones/{comision_id}")
def administrador_get_comision(context):
    _get(context, f"/comisiones/{context['comision'].id}", _headers_administrador())


@when("un Administrador hace GET /comisiones/{id-inexistente}")
def administrador_get_comision_inexistente(context):
    _get(context, f"/comisiones/{context['comision_id']}", _headers_administrador())


@when(parsers.parse("un Administrador hace POST /comisiones/{{comision_id}}/docentes con {resto}"))
def administrador_post_docentes(context, resto):
    docente_id = context["usuario"].id if "usuario" in context else context["docente"].id
    _post(
        context,
        f"/comisiones/{context['comision'].id}/docentes",
        {"docente_id": str(docente_id)},
        _headers_administrador(),
    )


@when("un Docente hace GET /comisiones/{comision_id}")
def docente_get_comision(context):
    _get(context, f"/comisiones/{context['comision'].id}", _headers_docente())


@when("hace GET /comisiones/{comision_id}")
def estudiante_get_comision(context):
    _get(context, f"/comisiones/{context['comision'].id}", _headers_estudiante())


@then("recibe 200 con docentes_asignados vacío")
def valida_200_sin_docente(context):
    response = context["response"]
    assert response.status_code == 200
    assert response.json()["docentes_asignados"] == []


@then("recibe 200 con el id del docente asignado")
def valida_200_con_docente(context):
    response = context["response"]
    assert response.status_code == 200
    assert response.json()["docentes_asignados"] == [str(context["docente"].id)]


@then("recibe 200 con el docente en docentes_asignados")
def valida_200_docente_asignado(context):
    response = context["response"]
    assert response.status_code == 200
    assert str(context["usuario"].id) in response.json()["docentes_asignados"]


@then("recibe 200 con el docente una sola vez en docentes_asignados")
def valida_200_docente_idempotente(context):
    response = context["response"]
    assert response.status_code == 200
    docentes = response.json()["docentes_asignados"]
    assert docentes.count(str(context["docente"].id)) == 1


@then("recibe 404")
def valida_404(context):
    assert context["response"].status_code == 404


@then("recibe 422")
def valida_422(context):
    assert context["response"].status_code == 422


@then("recibe 200")
def valida_200(context):
    assert context["response"].status_code == 200


@then("recibe 403")
def valida_403(context):
    assert context["response"].status_code == 403
