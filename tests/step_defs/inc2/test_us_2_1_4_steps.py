from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc2._auth_headers import docente_headers

scenarios("../../features/inc2/US-2.1.4-cargar-pregunta-verdadero-falso.feature")


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


async def _post_cargar_pregunta_verdadero_falso(banco_id: str, respuesta_correcta: bool):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            "/preguntas/verdadero-falso",
            json={
                "banco_id": banco_id,
                "texto": "El sol es una estrella.",
                "respuesta_correcta": respuesta_correcta,
                "unidad_tematica": "Unidad 1",
                "tema": "Astronomía",
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


@when("ejecuta CargarPreguntaVerdaderoFalso con respuesta_correcta = true")
def ejecuta_carga_respuesta_verdadero(context):
    context["response"] = run_async(
        _post_cargar_pregunta_verdadero_falso(context["banco_id"], True)
    )


@when("ejecuta CargarPreguntaVerdaderoFalso con respuesta_correcta = false")
def ejecuta_carga_respuesta_falso(context):
    context["response"] = run_async(
        _post_cargar_pregunta_verdadero_falso(context["banco_id"], False)
    )


@then("el sistema persiste la PreguntaPlantillaVerdaderoFalso con activa = true")
def valida_pregunta_persistida(context):
    assert context["response"].status_code == 201
    assert context["response"].json()["activa"] is True


@then("se emite el evento PreguntaCargada")
def valida_evento_emitido(context):
    assert context["response"].status_code == 201
