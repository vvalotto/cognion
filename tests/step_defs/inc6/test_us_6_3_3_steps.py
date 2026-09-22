"""Steps BDD de `US-6.3.3` — Estado completo de la sesión para reconectar la proyección."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from tests.integration.inc6._helpers import (
    cerrar_pregunta_actual,
    crear_estudiante,
    headers_de,
    iniciar_sesion,
    mostrar_opciones,
    pregunta_actual_de,
    preparar_sesion,
    unirse_a_sesion,
)

scenarios("../../features/inc6/US-6.3.3-estado-completo-reconexion-proyeccion.feature")


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


def _docente() -> dict[str, str]:
    return headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)


async def _get(sesion_id: str, headers: dict[str, str]):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(f"/sesiones-en-vivo/{sesion_id}", headers=headers)


async def _responder(
    sesion_id: str, headers: dict[str, str], pregunta_id: str, opcion: int
) -> dict:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        respuesta = await client.post(
            f"/sesiones-en-vivo/{sesion_id}/responder",
            json={"pregunta_id": pregunta_id, "contenido": {"opcion_indice": opcion}},
            headers=headers,
        )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


@given("una sesión con 5 participantes y 3 respuestas a la pregunta actual")
def sesion_con_participantes_y_respuestas(context):
    async def _armar() -> None:
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)
        pregunta_id = await pregunta_actual_de(sesion_id)
        for i in range(5):
            _, headers = await crear_estudiante(comision_id)
            await unirse_a_sesion(sesion_id, headers)
            if i < 3:
                await _responder(sesion_id, headers, pregunta_id, 1)
        context["sesion_id"] = sesion_id

    run_async(_armar())


@given("una sesión EnEspera")
def sesion_en_espera(context):
    sesion_id, _ = run_async(preparar_sesion(opcion_multiple=True))
    context["sesion_id"] = sesion_id


@given("una pregunta cerrada con respuestas registradas")
def pregunta_cerrada_con_respuestas(context):
    async def _armar() -> None:
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)
        _, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)
        await _responder(sesion_id, headers, await pregunta_actual_de(sesion_id), 1)
        await cerrar_pregunta_actual(sesion_id)
        context.update(sesion_id=sesion_id, headers_estudiante=headers)

    run_async(_armar())


@given("una pregunta con las opciones mostradas y sin cerrar")
def pregunta_abierta_sin_cerrar(context):
    async def _armar() -> None:
        sesion_id, _ = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)
        context["sesion_id"] = sesion_id

    run_async(_armar())


@given("una pregunta cerrada")
def pregunta_cerrada(context):
    async def _armar() -> None:
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_sesion(sesion_id)
        await mostrar_opciones(sesion_id)
        _, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)
        await _responder(sesion_id, headers, await pregunta_actual_de(sesion_id), 1)
        await cerrar_pregunta_actual(sesion_id)
        context.update(sesion_id=sesion_id, headers_estudiante=headers)

    run_async(_armar())


@given("un cliente que consume solo los campos de US-6.2.8")
def cliente_de_us_6_2_8(context):
    sesion_id, _ = run_async(preparar_sesion(opcion_multiple=True))
    context["sesion_id"] = sesion_id


@when("el Docente consulta el estado")
def docente_consulta_estado(context):
    context["response"] = run_async(_get(context["sesion_id"], _docente()))


@when("se consulta el estado")
def se_consulta_estado(context):
    context["response"] = run_async(_get(context["sesion_id"], _docente()))


@when("un Estudiante consulta el estado")
def estudiante_consulta_estado(context):
    context["response"] = run_async(_get(context["sesion_id"], context["headers_estudiante"]))


@when("consulta el estado")
def consulta_estado(context):
    context["response"] = run_async(_get(context["sesion_id"], _docente()))


@then("total_participantes es 5 y cantidad_respuestas es 3")
def total_participantes_y_cantidad_respuestas(context):
    cuerpo = context["response"].json()
    assert context["response"].status_code == 200
    assert cuerpo["total_participantes"] == 5
    assert cuerpo["cantidad_respuestas"] == 3


@then("cantidad_respuestas es 0 y resultado_pregunta es nulo")
def cantidad_respuestas_cero_y_resultado_nulo(context):
    cuerpo = context["response"].json()
    assert cuerpo["cantidad_respuestas"] == 0
    assert cuerpo["resultado_pregunta"] is None


@then("resultado_pregunta trae la distribución y el ranking con nombres")
def resultado_trae_distribucion_y_ranking(context):
    resultado = context["response"].json()["resultado_pregunta"]
    assert resultado is not None
    assert len(resultado["distribucion"]) >= 1
    assert len(resultado["ranking"]) == 1
    assert resultado["ranking"][0]["nombre"] == "Estudiante"


@then("resultado_pregunta es nulo")
def resultado_pregunta_es_nulo(context):
    assert context["response"].json()["resultado_pregunta"] is None


@then("recibe los mismos campos de siempre")
def recibe_los_mismos_campos_de_siempre(context):
    cuerpo = context["response"].json()
    assert context["response"].status_code == 200
    assert cuerpo["estado"] == "EnEspera"
    assert cuerpo["pregunta_actual"] is None
    assert cuerpo["cantidad_preguntas"] == 5
    assert cuerpo["ya_respondio"] is None
