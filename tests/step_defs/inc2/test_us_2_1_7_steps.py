from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc2._auth_headers import docente_headers

scenarios("../../features/inc2/US-2.1.7-filtrar-banco.feature")


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


async def _post_cargar_pregunta_opcion_multiple(
    banco_id: str, dificultad: str = "medio", importancia: str = "alto"
):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            "/preguntas/opcion-multiple",
            json={
                "banco_id": banco_id,
                "texto": "¿Cuál es la capital de Entre Ríos?",
                "opciones": [
                    {"texto": "Paraná", "es_correcta": True},
                    {"texto": "Concordia", "es_correcta": False},
                ],
                "unidad_tematica": "Unidad 1",
                "tema": "Arquitectura",
                "dificultad": dificultad,
                "importancia": importancia,
            },
            headers=docente_headers(),
        )


async def _delete_eliminar_pregunta(pregunta_id: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.delete(f"/preguntas/{pregunta_id}", headers=docente_headers())


async def _get_filtrar_banco(banco_id: str, **filtros):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(
            f"/bancos/{banco_id}/preguntas", params=filtros, headers=docente_headers()
        )


@given("un Docente autenticado")
def docente_autenticado(context):
    context["headers"] = docente_headers()


@given("un Banco con preguntas de distinta dificultad e importancia")
def banco_con_preguntas_mixtas(context):
    respuesta_materia = run_async(_post_crear_materia("Ingeniería de Software"))
    assert respuesta_materia.status_code == 201
    banco_id = respuesta_materia.json()["banco_id"]
    context["banco_id"] = banco_id

    match = run_async(
        _post_cargar_pregunta_opcion_multiple(banco_id, dificultad="alto", importancia="alto")
    )
    assert match.status_code == 201
    context["match_id"] = match.json()["id"]

    otra = run_async(
        _post_cargar_pregunta_opcion_multiple(banco_id, dificultad="bajo", importancia="alto")
    )
    assert otra.status_code == 201


@given("un Banco con 5 preguntas activas y 1 inactiva")
def banco_con_activas_e_inactiva(context):
    respuesta_materia = run_async(_post_crear_materia("Gestión de Proyectos"))
    assert respuesta_materia.status_code == 201
    banco_id = respuesta_materia.json()["banco_id"]
    context["banco_id"] = banco_id

    activas_ids = []
    for _ in range(5):
        respuesta = run_async(_post_cargar_pregunta_opcion_multiple(banco_id))
        assert respuesta.status_code == 201
        activas_ids.append(respuesta.json()["id"])
    context["activas_ids"] = activas_ids

    inactiva = run_async(_post_cargar_pregunta_opcion_multiple(banco_id))
    assert inactiva.status_code == 201
    inactiva_id = inactiva.json()["id"]
    eliminacion = run_async(_delete_eliminar_pregunta(inactiva_id))
    assert eliminacion.status_code == 204
    context["inactiva_id"] = inactiva_id


@given('un Banco sin preguntas de dificultad "Bajo"')
def banco_sin_preguntas_bajo(context):
    respuesta_materia = run_async(_post_crear_materia("Analytics"))
    assert respuesta_materia.status_code == 201
    banco_id = respuesta_materia.json()["banco_id"]
    context["banco_id"] = banco_id

    respuesta = run_async(_post_cargar_pregunta_opcion_multiple(banco_id, dificultad="alto"))
    assert respuesta.status_code == 201


@when('ejecuta FiltrarBanco con dificultad "Alto" e importancia "Alto"')
def ejecuta_filtrar_banco_dificultad_importancia(context):
    context["response"] = run_async(
        _get_filtrar_banco(context["banco_id"], dificultad="alto", importancia="alto")
    )


@when("ejecuta FiltrarBanco sin más filtros que la materia")
def ejecuta_filtrar_banco_sin_filtros(context):
    context["response"] = run_async(_get_filtrar_banco(context["banco_id"]))


@when('ejecuta FiltrarBanco con dificultad "Bajo"')
def ejecuta_filtrar_banco_dificultad_bajo(context):
    context["response"] = run_async(_get_filtrar_banco(context["banco_id"], dificultad="bajo"))


@then("el sistema devuelve solo las preguntas activas que matchean ambos filtros")
def valida_solo_matchean_ambos_filtros(context):
    assert context["response"].status_code == 200
    data = context["response"].json()
    assert [p["id"] for p in data] == [context["match_id"]]


@then("el sistema devuelve las 5 preguntas activas")
def valida_devuelve_cinco_activas(context):
    assert context["response"].status_code == 200
    data = context["response"].json()
    assert {p["id"] for p in data} == set(context["activas_ids"])


@then("no incluye la pregunta inactiva")
def valida_no_incluye_inactiva(context):
    data = context["response"].json()
    assert context["inactiva_id"] not in [p["id"] for p in data]


@then("el sistema devuelve una lista vacía")
def valida_lista_vacia(context):
    assert context["response"].status_code == 200
    assert context["response"].json() == []
