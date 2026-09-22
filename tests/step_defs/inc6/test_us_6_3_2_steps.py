"""Steps BDD de `US-6.3.2` — Listar las sesiones en vivo de una Comisión."""

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
from tests.integration.inc6._helpers import (
    crear_estudiante,
    headers_de,
    iniciar_sesion,
    iniciar_y_finalizar,
    preparar_sesion,
)

scenarios("../../features/inc6/US-6.3.2-listar-sesiones-en-vivo-comision.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM comision_docentes"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM materia"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM usuario"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_sesion_en_vivo():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {}


def _cliente() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _docente() -> dict[str, str]:
    return headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)


async def _get(params: dict, headers: dict[str, str]):
    async with _cliente() as client:
        return await client.get("/sesiones-en-vivo", params=params, headers=headers)


async def _crear_sesion(comision_id: str) -> str:
    """Crea una sesión adicional sobre una Comisión ya existente (mismo banco de preguntas)."""
    async with _cliente() as client:
        respuesta = await client.post(
            "/sesiones-en-vivo",
            json={
                "comision_id": comision_id,
                "cantidad_preguntas": 5,
                "tiempo_limite_por_pregunta_segundos": 30,
            },
            headers=_docente(),
        )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["id"]


async def _crear_comision_sin_sesion() -> str:
    """Crea una Materia + Comisión reales, sin ninguna sesión en vivo."""
    admin = headers_de(uuid.uuid4(), TipoPerfil.ADMINISTRADOR)
    async with _cliente() as client:
        creada = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=admin
        )
    materia_id = creada.json()["id"]
    async with SessionLocal() as session:
        admin_usuario = Usuario.crear(
            "Admin",
            f"admin.{uuid.uuid4()}@fiuner.edu.ar",
            BcryptPasswordHasher().hash("x"),
            TipoPerfil.ADMINISTRADOR,
        )
        await SQLAlchemyUsuarioRepository(session).guardar(admin_usuario)
        comision = Comision.crear(uuid.UUID(materia_id), "lu 10-12", admin_usuario.id)
        await SQLAlchemyComisionRepository(session).guardar(comision)
    return str(comision.id)


@given("una sesión EnEspera y otra EnCurso de la Comisión del Estudiante")
def sesion_en_espera_y_en_curso(context):
    async def _armar() -> None:
        en_espera, comision_id = await preparar_sesion()
        en_curso = await _crear_sesion(comision_id)
        await iniciar_sesion(en_curso)
        _, headers = await crear_estudiante(comision_id)
        context.update(
            sesion_en_espera=en_espera,
            sesion_en_curso=en_curso,
            headers_estudiante=headers,
        )

    run_async(_armar())


@given("una sesión activa de otra Comisión")
def sesion_activa_de_otra_comision(context):
    async def _armar() -> None:
        await preparar_sesion()
        comision_propia = await _crear_comision_sin_sesion()
        _, headers = await crear_estudiante(comision_propia)
        context.update(headers_estudiante=headers)

    run_async(_armar())


@given("una sesión Finalizada de la Comisión")
def sesion_finalizada_de_la_comision(context):
    async def _armar() -> None:
        sesion_id, comision_id = await preparar_sesion()
        await iniciar_y_finalizar(sesion_id)
        _, headers = await crear_estudiante(comision_id)
        context.update(sesion_id=sesion_id, comision_id=comision_id, headers_estudiante=headers)

    run_async(_armar())


@given("una sesión EnCurso de la Comisión")
def sesion_en_curso_de_la_comision(context):
    async def _armar() -> None:
        sesion_id, comision_id = await preparar_sesion()
        await iniciar_sesion(sesion_id)
        context.update(sesion_id=sesion_id, comision_id=comision_id)

    run_async(_armar())


@given("un Docente autenticado")
def docente_autenticado(context):
    context["headers_docente"] = _docente()


@given("un Estudiante autenticado")
def estudiante_autenticado(context):
    async def _armar() -> None:
        _, comision_propia = await preparar_sesion()
        _, comision_de_otro = await preparar_sesion()
        _, headers = await crear_estudiante(comision_propia)
        context.update(comision_de_otro=comision_de_otro, headers_estudiante=headers)

    run_async(_armar())


@given("una Comisión sin sesiones activas")
def comision_sin_sesiones_activas(context):
    comision_id = run_async(_crear_comision_sin_sesion())
    context["comision_id"] = comision_id


@given("dos sesiones activas creadas en momentos distintos")
def dos_sesiones_activas(context):
    async def _armar() -> None:
        primera, comision_id = await preparar_sesion()
        segunda = await _crear_sesion(comision_id)
        context.update(primera=primera, segunda=segunda, comision_id=comision_id)

    run_async(_armar())


@when("el Estudiante lista las sesiones")
def estudiante_lista_sesiones(context):
    context["response"] = run_async(_get({}, context["headers_estudiante"]))


@when("el Docente lista las sesiones pasando la Comisión")
def docente_lista_pasando_comision(context):
    context["response"] = run_async(
        _get({"comision_id": context["comision_id"]}, _docente())
    )


@when("el Docente lista con estado Finalizada")
def docente_lista_con_estado_finalizada(context):
    context["response"] = run_async(
        _get({"comision_id": context["comision_id"], "estado": "Finalizada"}, _docente())
    )


@when("lista las sesiones sin comision_id")
def lista_sin_comision_id(context):
    context["response"] = run_async(_get({}, context["headers_docente"]))


@when("lista las sesiones pasando la comision_id de otra Comisión")
def lista_pasando_comision_de_otro(context):
    context["response"] = run_async(
        _get({"comision_id": context["comision_de_otro"]}, context["headers_estudiante"])
    )


@when("se listan")
def se_listan(context):
    context["response"] = run_async(_get({"comision_id": context["comision_id"]}, _docente()))


@then("recibe las dos, con el nombre de la Materia y el estado")
def recibe_las_dos(context):
    assert context["response"].status_code == 200
    cuerpo = context["response"].json()
    ids = {s["id"]: s for s in cuerpo}
    assert set(ids) == {context["sesion_en_espera"], context["sesion_en_curso"]}
    assert ids[context["sesion_en_espera"]]["estado"] == "EnEspera"
    assert ids[context["sesion_en_curso"]]["estado"] == "EnCurso"
    assert all(s["materia_nombre"] for s in cuerpo)


@then("no aparece")
def no_aparece(context):
    assert context["response"].status_code == 200
    assert context["response"].json() == []


@then("recibe esa sesión con su estado")
def recibe_esa_sesion_con_su_estado(context):
    assert context["response"].status_code == 200
    cuerpo = context["response"].json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["id"] == context["sesion_id"]
    assert cuerpo[0]["estado"] == "EnCurso"


@then("recibe esa sesión")
def recibe_esa_sesion(context):
    assert context["response"].status_code == 200
    cuerpo = context["response"].json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["id"] == context["sesion_id"]
    assert cuerpo[0]["estado"] == "Finalizada"


@then(parsers.parse("el sistema responde {codigo:d}"))
def sistema_responde(context, codigo):
    assert context["response"].status_code == codigo


@then("la respuesta es una lista vacía")
def respuesta_es_lista_vacia(context):
    assert context["response"].status_code == 200
    assert context["response"].json() == []


@then("la más reciente aparece primero")
def la_mas_reciente_aparece_primero(context):
    assert context["response"].status_code == 200
    ids = [s["id"] for s in context["response"].json()]
    assert ids == [context["segunda"], context["primera"]]
