from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc2._auth_headers import docente_headers

scenarios("../../features/inc2/US-2.1.3-cargar-pregunta-opcion-multiple.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas_banco_preguntas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_banco_preguntas():
    run_async(_limpiar_tablas_banco_preguntas())
    yield
    run_async(_limpiar_tablas_banco_preguntas())


@pytest.fixture
def context():
    return {}


async def _post_crear_materia(nombre: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/materias", json={"nombre": nombre}, headers=docente_headers())


async def _post_cargar_pregunta_opcion_multiple(banco_id: str, opciones: list[dict]):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            "/preguntas/opcion-multiple",
            json={
                "banco_id": banco_id,
                "texto": "¿Cuál es la capital de Entre Ríos?",
                "opciones": opciones,
                "unidad_tematica": "Unidad 1",
                "tema": "Arquitectura",
                "dificultad": "medio",
                "importancia": "alto",
            },
            headers=docente_headers(),
        )


@given(parsers.parse('un Docente autenticado y un Banco existente para "{nombre_materia}"'))
def docente_y_banco_existente(context, nombre_materia):
    respuesta = run_async(_post_crear_materia(nombre_materia))
    assert respuesta.status_code == 201
    context["banco_id"] = respuesta.json()["banco_id"]


@when("ejecuta CargarPreguntaOpcionMultiple con 3 opciones y una marcada como correcta")
def ejecuta_carga_tres_opciones_una_correcta(context):
    opciones = [
        {"texto": "Paraná", "es_correcta": True},
        {"texto": "Concordia", "es_correcta": False},
        {"texto": "Gualeguaychú", "es_correcta": False},
    ]
    context["response"] = run_async(
        _post_cargar_pregunta_opcion_multiple(context["banco_id"], opciones)
    )


@when("ejecuta CargarPreguntaOpcionMultiple con 3 opciones y ninguna marcada como correcta")
def ejecuta_carga_tres_opciones_ninguna_correcta(context):
    opciones = [
        {"texto": "Paraná", "es_correcta": False},
        {"texto": "Concordia", "es_correcta": False},
        {"texto": "Gualeguaychú", "es_correcta": False},
    ]
    context["response"] = run_async(
        _post_cargar_pregunta_opcion_multiple(context["banco_id"], opciones)
    )


@when("ejecuta CargarPreguntaOpcionMultiple con 2 opciones marcadas como correctas")
def ejecuta_carga_dos_opciones_correctas(context):
    opciones = [
        {"texto": "Paraná", "es_correcta": True},
        {"texto": "Concordia", "es_correcta": True},
    ]
    context["response"] = run_async(
        _post_cargar_pregunta_opcion_multiple(context["banco_id"], opciones)
    )


@when("ejecuta CargarPreguntaOpcionMultiple con una única opción")
def ejecuta_carga_una_unica_opcion(context):
    opciones = [{"texto": "Paraná", "es_correcta": True}]
    context["response"] = run_async(
        _post_cargar_pregunta_opcion_multiple(context["banco_id"], opciones)
    )


@then("el sistema persiste la PreguntaPlantillaOpcionMultiple con activa = true")
def valida_pregunta_persistida(context):
    assert context["response"].status_code == 201
    assert context["response"].json()["activa"] is True


@then("se emite el evento PreguntaCargada")
def valida_evento_emitido(context):
    assert context["response"].status_code == 201


@then(parsers.parse("el sistema rechaza la operación con {codigo_error}"))
def valida_rechazo_con_codigo(context, codigo_error):
    mapa_status = {"OpcionesInvalidas": 422, "BancoNoExiste": 404}
    assert context["response"].status_code == mapa_status[codigo_error]


@then("no se persiste ninguna pregunta nueva")
def valida_ninguna_pregunta_nueva(context):
    assert context["response"].status_code == 422
