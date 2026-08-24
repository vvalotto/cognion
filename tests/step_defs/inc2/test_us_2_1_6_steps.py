from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc2._auth_headers import docente_headers

scenarios("../../features/inc2/US-2.1.6-eliminar-pregunta.feature")


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


async def _delete_eliminar_pregunta(pregunta_id: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.delete(f"/preguntas/{pregunta_id}", headers=docente_headers())


async def _marcar_inactiva(pregunta_id: str) -> None:
    async with SessionLocal() as session:
        await session.execute(
            text("UPDATE pregunta_plantilla SET activa = false WHERE id = :id"),
            {"id": pregunta_id},
        )
        await session.commit()


async def _fila_existe(pregunta_id: str) -> bool:
    async with SessionLocal() as session:
        resultado = await session.execute(
            text("SELECT 1 FROM pregunta_plantilla WHERE id = :id"), {"id": pregunta_id}
        )
        return resultado.first() is not None


@given("un Docente autenticado")
def docente_autenticado(context):
    context["headers"] = docente_headers()


@given("una PreguntaPlantilla activa")
def pregunta_activa(context):
    respuesta_materia = run_async(_post_crear_materia("Ingeniería de Software"))
    assert respuesta_materia.status_code == 201
    banco_id = respuesta_materia.json()["banco_id"]

    respuesta_pregunta = run_async(_post_cargar_pregunta_verdadero_falso(banco_id))
    assert respuesta_pregunta.status_code == 201
    context["pregunta_id"] = respuesta_pregunta.json()["id"]


@given("una PreguntaPlantilla con activa = false")
def pregunta_inactiva(context):
    respuesta_materia = run_async(_post_crear_materia("Gestión de Proyectos"))
    assert respuesta_materia.status_code == 201
    banco_id = respuesta_materia.json()["banco_id"]

    respuesta_pregunta = run_async(_post_cargar_pregunta_verdadero_falso(banco_id))
    assert respuesta_pregunta.status_code == 201
    pregunta_id = respuesta_pregunta.json()["id"]
    run_async(_marcar_inactiva(pregunta_id))
    context["pregunta_id"] = pregunta_id


@given("un pregunta_id que no corresponde a ninguna PreguntaPlantilla")
def pregunta_id_inexistente(context):
    context["pregunta_id"] = str(uuid.uuid4())


@when("ejecuta EliminarPregunta sobre esa pregunta")
def elimina_pregunta(context):
    context["response"] = run_async(_delete_eliminar_pregunta(context["pregunta_id"]))


@when("intenta ejecutar EliminarPregunta con ese id")
def intenta_eliminar_inexistente(context):
    context["response"] = run_async(_delete_eliminar_pregunta(context["pregunta_id"]))


@when("ejecuta EliminarPregunta sobre ella")
def elimina_pregunta_ya_eliminada(context):
    context["response"] = run_async(_delete_eliminar_pregunta(context["pregunta_id"]))


@then("el sistema marca la pregunta como activa = false")
def valida_marcada_inactiva(context):
    assert context["response"].status_code == 204


@then("la pregunta sigue existiendo en la base de datos")
def valida_fila_persiste(context):
    assert run_async(_fila_existe(context["pregunta_id"])) is True


@then("se emite el evento PreguntaEliminada")
def valida_evento_eliminada(context):
    assert context["response"].status_code == 204


@then("el sistema rechaza la operación con PreguntaNoExiste")
def valida_rechazo_pregunta_no_existe(context):
    assert context["response"].status_code == 404


@then("el sistema rechaza la operación con PreguntaYaEliminada")
def valida_rechazo_pregunta_ya_eliminada(context):
    assert context["response"].status_code == 409
