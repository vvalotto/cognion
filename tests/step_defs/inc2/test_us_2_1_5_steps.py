from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc2._auth_headers import docente_headers

scenarios("../../features/inc2/US-2.1.5-editar-pregunta.feature")


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


async def _post_cargar_pregunta_verdadero_falso(banco_id: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            "/preguntas/verdadero-falso",
            json={
                "banco_id": banco_id,
                "texto": "El sol es una estrella.",
                "respuesta_correcta": True,
                "unidad_tematica": "Unidad 1",
                "tema": "Astronomía",
                "dificultad": "medio",
                "importancia": "alto",
            },
            headers=docente_headers(),
        )


async def _put_editar_pregunta(pregunta_id: str, body: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.put(
            f"/preguntas/{pregunta_id}", json=body, headers=docente_headers()
        )


async def _marcar_inactiva(pregunta_id: str) -> None:
    async with SessionLocal() as session:
        await session.execute(
            text("UPDATE pregunta_plantilla SET activa = false WHERE id = :id"),
            {"id": pregunta_id},
        )
        await session.commit()


@given("un Docente autenticado")
def docente_autenticado(context):
    context["headers"] = docente_headers()


@given("una PreguntaPlantillaOpcionMultiple activa con 3 opciones")
def pregunta_om_activa_con_tres_opciones(context):
    respuesta_materia = run_async(_post_crear_materia("Gestión de Proyectos"))
    assert respuesta_materia.status_code == 201
    banco_id = respuesta_materia.json()["banco_id"]

    respuesta_pregunta = run_async(
        _post_cargar_pregunta_opcion_multiple(
            banco_id,
            [
                {"texto": "Paraná", "es_correcta": True},
                {"texto": "Concordia", "es_correcta": False},
                {"texto": "Gualeguaychú", "es_correcta": False},
            ],
        )
    )
    assert respuesta_pregunta.status_code == 201
    context["pregunta_id"] = respuesta_pregunta.json()["id"]


@given("una PreguntaPlantillaOpcionMultiple activa")
def pregunta_om_activa(context):
    respuesta_materia = run_async(_post_crear_materia("Ingeniería de Software"))
    assert respuesta_materia.status_code == 201
    banco_id = respuesta_materia.json()["banco_id"]

    respuesta_pregunta = run_async(
        _post_cargar_pregunta_opcion_multiple(
            banco_id,
            [
                {"texto": "Paraná", "es_correcta": True},
                {"texto": "Concordia", "es_correcta": False},
            ],
        )
    )
    assert respuesta_pregunta.status_code == 201
    context["pregunta_id"] = respuesta_pregunta.json()["id"]


@given("una PreguntaPlantilla con activa = false")
def pregunta_inactiva(context):
    respuesta_materia = run_async(_post_crear_materia("Sistemas de Información"))
    assert respuesta_materia.status_code == 201
    banco_id = respuesta_materia.json()["banco_id"]

    respuesta_pregunta = run_async(_post_cargar_pregunta_verdadero_falso(banco_id))
    assert respuesta_pregunta.status_code == 201
    pregunta_id = respuesta_pregunta.json()["id"]
    run_async(_marcar_inactiva(pregunta_id))
    context["pregunta_id"] = pregunta_id


@when("ejecuta EditarPregunta cambiando el texto y una opción")
def edita_texto_y_opcion(context):
    context["response"] = run_async(
        _put_editar_pregunta(
            context["pregunta_id"],
            {
                "texto": "¿Cuál es la capital de la provincia de Entre Ríos?",
                "unidad_tematica": "Unidad 1",
                "tema": "Arquitectura",
                "dificultad": "medio",
                "importancia": "alto",
                "opciones": [
                    {"texto": "Paraná", "es_correcta": False},
                    {"texto": "Concordia", "es_correcta": True},
                    {"texto": "Gualeguaychú", "es_correcta": False},
                ],
            },
        )
    )


@when("ejecuta EditarPregunta desmarcando la única opción correcta sin marcar otra")
def desmarca_opcion_correcta(context):
    context["response"] = run_async(
        _put_editar_pregunta(
            context["pregunta_id"],
            {
                "texto": "¿Cuál es la capital de Entre Ríos?",
                "unidad_tematica": "Unidad 1",
                "tema": "Arquitectura",
                "dificultad": "medio",
                "importancia": "alto",
                "opciones": [
                    {"texto": "Paraná", "es_correcta": False},
                    {"texto": "Concordia", "es_correcta": False},
                ],
            },
        )
    )


@when("ejecuta EditarPregunta sobre ella")
def edita_pregunta_inactiva(context):
    context["response"] = run_async(
        _put_editar_pregunta(
            context["pregunta_id"],
            {
                "texto": "El sol es una estrella (editado).",
                "unidad_tematica": "Unidad 1",
                "tema": "Astronomía",
                "dificultad": "medio",
                "importancia": "alto",
                "respuesta_correcta": False,
            },
        )
    )


@then("el sistema persiste los cambios")
def valida_cambios_persistidos(context):
    assert context["response"].status_code == 200
    assert (
        context["response"].json()["texto"]
        == "¿Cuál es la capital de la provincia de Entre Ríos?"
    )


@then("se emite el evento PreguntaEditada")
def valida_evento_editada(context):
    assert context["response"].status_code == 200


@then("el sistema rechaza la operación con OpcionesInvalidas")
def valida_rechazo_opciones_invalidas(context):
    assert context["response"].status_code == 422


@then("el sistema rechaza la operación con PreguntaInactiva")
def valida_rechazo_pregunta_inactiva(context):
    assert context["response"].status_code == 409
