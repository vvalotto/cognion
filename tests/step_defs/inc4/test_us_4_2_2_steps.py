"""Steps BDD de US-4.2.2 (`tests/features/inc4/US-4.2.2-comision-query-port.feature`)."""

from __future__ import annotations

import asyncio
import uuid
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.analytics.frameworks.adapters.comision_consulta_port_in_process import (
    ComisionConsultaPortInProcess,
)
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

scenarios("../../features/inc4/US-4.2.2-comision-query-port.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM estudiante"))
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


def _headers_docente() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid4(), TipoPerfil.DOCENTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


def _headers_estudiante() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid4(), TipoPerfil.ESTUDIANTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


async def _crear_admin(session) -> Usuario:
    hasher = BcryptPasswordHasher()
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    return admin


async def _crear_materia_real() -> uuid.UUID:
    """Crea una `Materia` real vía HTTP — `MateriaPort.obtener()` la exige para el 200/404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=_headers_docente()
        )
    return uuid.UUID(response.json()["id"])


async def _crear_materia_con_comisiones(cantidad: int) -> tuple[uuid.UUID, list[Comision]]:
    materia_id = await _crear_materia_real()
    async with SessionLocal() as session:
        admin = await _crear_admin(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        comisiones = [
            Comision.crear(materia_id, f"horario {i}", admin.id) for i in range(cantidad)
        ]
        for comision in comisiones:
            await comision_repo.guardar(comision)
        return materia_id, comisiones


async def _crear_comision_con_estudiantes(cantidad: int) -> tuple[Comision, list[Usuario]]:
    async with SessionLocal() as session:
        admin = await _crear_admin(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        hasher = BcryptPasswordHasher()
        comision = Comision.crear(uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        estudiantes = []
        for i in range(cantidad):
            estudiante = Usuario.crear_estudiante(
                f"Estudiante {i}", f"est.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
            )
            await usuario_repo.guardar(estudiante)
            estudiantes.append(estudiante)
        return comision, estudiantes


async def _crear_comision_vacia() -> Comision:
    async with SessionLocal() as session:
        admin = await _crear_admin(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        comision = Comision.crear(uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        return comision


def _get(context, path: str, headers) -> None:
    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(path, headers=headers)

    context["response"] = run_async(_call())


@given("una materia X con 2 comisiones")
def materia_con_2_comisiones(context):
    materia_id, comisiones = run_async(_crear_materia_con_comisiones(2))
    context["materia_id"] = materia_id
    context["comisiones"] = comisiones
    context["headers"] = _headers_docente()


@given("una comisión con 3 estudiantes inscriptos")
def comision_con_3_estudiantes(context):
    comision, estudiantes = run_async(_crear_comision_con_estudiantes(3))
    context["comision"] = comision
    context["estudiantes"] = estudiantes
    context["headers"] = _headers_docente()


@given("una comisión recién creada, sin inscripciones")
def comision_recien_creada(context):
    context["comision"] = run_async(_crear_comision_vacia())
    context["headers"] = _headers_docente()


@given("un id de materia que no existe")
def id_de_materia_inexistente(context):
    context["materia_id"] = uuid4()
    context["headers"] = _headers_docente()


@given("un Estudiante autenticado")
def estudiante_autenticado(context):
    materia_id, _ = run_async(_crear_materia_con_comisiones(1))
    context["materia_id"] = materia_id
    context["headers"] = _headers_estudiante()


@given('el mismo estado de datos que el escenario "Materia con comisiones"')
def mismo_estado_que_materia_con_comisiones(context):
    materia_id, comisiones = run_async(_crear_materia_con_comisiones(2))
    context["materia_id"] = materia_id
    context["comisiones"] = comisiones
    context["headers"] = _headers_docente()


@when("un Docente hace GET /materias/X/comisiones")
def docente_get_comisiones_de_materia(context):
    _get(context, f"/materias/{context['materia_id']}/comisiones", context["headers"])


@when("un Docente hace GET /comisiones/{comision_id}/estudiantes")
def docente_get_estudiantes_de_comision(context):
    _get(context, f"/comisiones/{context['comision'].id}/estudiantes", context["headers"])


@when("un Docente hace GET /materias/{id-inexistente}/comisiones")
def docente_get_comisiones_materia_inexistente(context):
    _get(context, f"/materias/{context['materia_id']}/comisiones", context["headers"])


@when("hace GET /materias/X/comisiones")
def get_comisiones_de_materia(context):
    _get(context, f"/materias/{context['materia_id']}/comisiones", context["headers"])


@when("ComisionConsultaPort.listar_comisiones_por_materia(X) se invoca in-process")
def invocar_puerto_in_process(context):
    async def _invocar():
        async with SessionLocal() as session:
            port = ComisionConsultaPortInProcess(session)
            return await port.listar_comisiones_por_materia(context["materia_id"])

    context["resultado_in_process"] = run_async(_invocar())


@then("recibe 200 con las 2 comisiones (id, horario)")
def valida_200_con_2_comisiones(context):
    response = context["response"]
    assert response.status_code == 200
    ids_esperados = {str(c.id) for c in context["comisiones"]}
    ids_recibidos = {c["id"] for c in response.json()}
    assert ids_recibidos == ids_esperados
    assert all("horario" in c for c in response.json())


@then("recibe 200 con los 3 estudiantes")
def valida_200_con_3_estudiantes(context):
    response = context["response"]
    assert response.status_code == 200
    ids_esperados = {str(e.id) for e in context["estudiantes"]}
    ids_recibidos = {e["id"] for e in response.json()}
    assert ids_recibidos == ids_esperados


@then("recibe 200 con lista vacía")
def valida_200_con_lista_vacia(context):
    response = context["response"]
    assert response.status_code == 200
    assert response.json() == []


@then("recibe 404")
def valida_404(context):
    assert context["response"].status_code == 404


@then("recibe 403")
def valida_403(context):
    assert context["response"].status_code == 403


@then("devuelve el mismo resultado que el endpoint HTTP equivalente")
def valida_mismo_resultado_que_http(context):
    async def _via_http():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(
                f"/materias/{context['materia_id']}/comisiones", headers=context["headers"]
            )

    respuesta_http = run_async(_via_http())
    assert respuesta_http.status_code == 200
    ids_http = {c["id"] for c in respuesta_http.json()}
    ids_in_process = {str(c.id) for c in context["resultado_in_process"]}
    assert ids_in_process == ids_http
