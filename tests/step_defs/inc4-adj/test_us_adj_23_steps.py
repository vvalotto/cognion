"""Steps BDD de US-ADJ-23 (`tests/features/inc4-adj/US-ADJ-23-listado-comisiones.feature`)."""

from __future__ import annotations

import asyncio
import uuid
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
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
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer

scenarios("../../features/inc4-adj/US-ADJ-23-listado-comisiones.feature")


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


async def _crear_materia_real() -> uuid.UUID:
    """Crea una `Materia` real vía HTTP — `MateriaPort.obtener()` la exige para el 200/404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=_headers_docente()
        )
    return uuid.UUID(response.json()["id"])


async def _crear_admin(session) -> Usuario:
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    return admin


async def _crear_materia_con_comision_y_docente(cantidad_estudiantes: int):
    materia_id = await _crear_materia_real()
    async with SessionLocal() as session:
        admin = await _crear_admin(session)
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        hasher = BcryptPasswordHasher()
        docente = Usuario.crear(
            "Docente", f"docente.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.DOCENTE
        )
        await usuario_repo.guardar(docente)
        comision = Comision.crear(materia_id, "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        comision.asignar_docente(docente.id)
        await comision_repo.actualizar(comision)
        for i in range(cantidad_estudiantes):
            estudiante = Usuario.crear_estudiante(
                f"Estudiante {i}",
                f"est.{uuid.uuid4()}@fiuner.edu.ar",
                hasher.hash("x"),
                comision.id,
            )
            await usuario_repo.guardar(estudiante)
        return materia_id, comision, docente


async def _crear_materia_con_comision_sin_docente():
    materia_id = await _crear_materia_real()
    async with SessionLocal() as session:
        admin = await _crear_admin(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        comision = Comision.crear(materia_id, "ma 14-16", admin.id)
        await comision_repo.guardar(comision)
        return materia_id, comision


def _get(context, path: str, headers) -> None:
    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(path, headers=headers)

    context["response"] = run_async(_call())


@given("una materia con una comisión que tiene un docente asignado y 3 estudiantes inscriptos")
def materia_con_comision_docente_y_estudiantes(context):
    materia_id, comision, docente = run_async(_crear_materia_con_comision_y_docente(3))
    context["materia_id"] = materia_id
    context["comision"] = comision
    context["docente"] = docente


@given("una materia con una comisión sin ningún docente asignado")
def materia_con_comision_sin_docente(context):
    materia_id, comision = run_async(_crear_materia_con_comision_sin_docente())
    context["materia_id"] = materia_id
    context["comision"] = comision


@given("una materia sin ninguna comisión")
def materia_sin_comisiones(context):
    context["materia_id"] = run_async(_crear_materia_real())


@given("un id de materia que no existe")
def id_de_materia_inexistente(context):
    context["materia_id"] = uuid4()


@given("una materia con una comisión")
def materia_con_una_comision(context):
    materia_id, comision = run_async(_crear_materia_con_comision_sin_docente())
    context["materia_id"] = materia_id
    context["comision"] = comision


@given("una comisión con estudiantes inscriptos")
def comision_con_estudiantes(context):
    _, comision, _docente = run_async(_crear_materia_con_comision_y_docente(2))
    context["comision"] = comision


@given("un Estudiante autenticado")
def estudiante_autenticado(context):
    materia_id, comision, _docente = run_async(_crear_materia_con_comision_y_docente(0))
    context["materia_id"] = materia_id
    context["comision"] = comision


@when("un Administrador hace GET /materias/{materia_id}/comisiones")
def administrador_get_comisiones(context):
    _get(context, f"/materias/{context['materia_id']}/comisiones", _headers_administrador())


@when("un Administrador hace GET /materias/{id-inexistente}/comisiones")
def administrador_get_comisiones_materia_inexistente(context):
    _get(context, f"/materias/{context['materia_id']}/comisiones", _headers_administrador())


@when("un Docente hace GET /materias/{materia_id}/comisiones")
def docente_get_comisiones(context):
    _get(context, f"/materias/{context['materia_id']}/comisiones", _headers_docente())


@when("un Docente hace GET /comisiones/{comision_id}/estudiantes")
def docente_get_estudiantes(context):
    _get(context, f"/comisiones/{context['comision'].id}/estudiantes", _headers_docente())


@when("hace GET /materias/{materia_id}/comisiones")
def estudiante_get_comisiones(context):
    _get(context, f"/materias/{context['materia_id']}/comisiones", _headers_estudiante())


@when("hace GET /comisiones/{comision_id}/estudiantes")
def estudiante_get_estudiantes(context):
    _get(context, f"/comisiones/{context['comision'].id}/estudiantes", _headers_estudiante())


@then("recibe 200 con la comisión, incluido el id del docente asignado")
def valida_200_con_docente_asignado(context):
    response = context["response"]
    assert response.status_code == 200
    comisiones = response.json()
    assert len(comisiones) == 1
    assert comisiones[0]["docentes_asignados"] == [str(context["docente"].id)]


@then("recibe 200 con la comisión y docentes_asignados vacío")
def valida_200_sin_docente_asignado(context):
    response = context["response"]
    assert response.status_code == 200
    comisiones = response.json()
    assert len(comisiones) == 1
    assert comisiones[0]["docentes_asignados"] == []


@then("recibe 200 con lista vacía")
def valida_200_lista_vacia(context):
    response = context["response"]
    assert response.status_code == 200
    assert response.json() == []


@then("recibe 404")
def valida_404(context):
    assert context["response"].status_code == 404


@then("recibe 200, mismo comportamiento que antes de esta US")
def valida_200_regresion(context):
    assert context["response"].status_code == 200


@then("recibe 200 con los estudiantes")
def valida_200_con_estudiantes(context):
    assert context["response"].status_code == 200


@then("recibe 403")
def valida_403(context):
    assert context["response"].status_code == 403
