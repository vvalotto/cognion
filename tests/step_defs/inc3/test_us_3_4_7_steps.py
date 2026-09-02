from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc3._auth_headers import crear_estudiante, docente_headers

scenarios("../../features/inc3/US-3.4.7-finalizar-revision.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.execute(text("DELETE FROM invitacion"))
        await session.execute(text("DELETE FROM comision_docentes"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM usuario"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_actividad_evaluativa_y_estudiantes():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {}


async def _crear_materia_con_preguntas(cantidad_correctas: int, cantidad_incorrectas: int) -> str:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        creada = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=docente_headers()
        )
        banco_id = creada.json()["banco_id"]

        for i in range(cantidad_correctas + cantidad_incorrectas):
            await client.post(
                "/preguntas/verdadero-falso",
                json={
                    "banco_id": banco_id,
                    "texto": f"Pregunta {i} {uuid.uuid4()}",
                    "respuesta_correcta": True,
                    "unidad_tematica": "Unidad 1",
                    "tema": "Tema",
                    "dificultad": "medio",
                    "importancia": "alto",
                },
                headers=docente_headers(),
            )

        return creada.json()["id"]


async def _crear_actividad(materia_id: str, cantidad_preguntas: int) -> str:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        apertura = datetime.now(UTC) - timedelta(days=1)
        cierre = apertura + timedelta(days=7)
        response = await client.post(
            "/actividades",
            json={
                "materia_id": materia_id,
                "fecha_apertura": apertura.isoformat(),
                "fecha_cierre": cierre.isoformat(),
                "cantidad_preguntas": cantidad_preguntas,
                "cantidad_intentos_permitidos": 1,
            },
            headers=docente_headers(),
        )
        return response.json()["id"]


async def _iniciar_evaluacion(actividad_id: str, estudiante_headers: dict) -> dict:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/evaluaciones", json={"actividad_id": actividad_id}, headers=estudiante_headers
        )
        return response.json()


async def _registrar_respuesta(
    evaluacion_id: str, pregunta_id: str, valor: bool, estudiante_headers: dict
):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            f"/evaluaciones/{evaluacion_id}/respuestas",
            json={"pregunta_id": pregunta_id, "contenido": {"valor": valor}},
            headers=estudiante_headers,
        )


async def _finalizar(evaluacion_id: str, estudiante_headers: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            f"/evaluaciones/{evaluacion_id}/finalizar", headers=estudiante_headers
        )


async def _obtener_revision(evaluacion_id: str, estudiante_headers: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(
            f"/evaluaciones/{evaluacion_id}/revision", headers=estudiante_headers
        )


@given("un Estudiante en la pantalla de rendir con al menos una pregunta respondida")
def estudiante_con_una_respondida(context):
    materia_id = run_async(_crear_materia_con_preguntas(1, 0))
    actividad_id = run_async(_crear_actividad(materia_id, 1))
    _estudiante_id, headers = run_async(crear_estudiante())
    evaluacion = run_async(_iniciar_evaluacion(actividad_id, headers))
    pregunta_id = evaluacion["preguntas_asignadas"][0]["pregunta_id"]
    run_async(_registrar_respuesta(evaluacion["id"], pregunta_id, True, headers))
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers


@given("una Evaluacion Finalizada con 7 respuestas correctas y 3 incorrectas")
def evaluacion_finalizada_7_3(context):
    materia_id = run_async(_crear_materia_con_preguntas(7, 3))
    actividad_id = run_async(_crear_actividad(materia_id, 10))
    _estudiante_id, headers = run_async(crear_estudiante())
    evaluacion = run_async(_iniciar_evaluacion(actividad_id, headers))
    preguntas = evaluacion["preguntas_asignadas"]
    for pregunta in preguntas[:7]:
        run_async(_registrar_respuesta(evaluacion["id"], pregunta["pregunta_id"], True, headers))
    for pregunta in preguntas[7:]:
        run_async(_registrar_respuesta(evaluacion["id"], pregunta["pregunta_id"], False, headers))
    run_async(_finalizar(evaluacion["id"], headers))
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers


@given("una actividad ya finalizada por el Estudiante")
def actividad_ya_finalizada(context):
    materia_id = run_async(_crear_materia_con_preguntas(1, 0))
    actividad_id = run_async(_crear_actividad(materia_id, 1))
    _estudiante_id, headers = run_async(crear_estudiante())
    evaluacion = run_async(_iniciar_evaluacion(actividad_id, headers))
    pregunta_id = evaluacion["preguntas_asignadas"][0]["pregunta_id"]
    run_async(_registrar_respuesta(evaluacion["id"], pregunta_id, True, headers))
    run_async(_finalizar(evaluacion["id"], headers))
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers


@when("elige finalizar")
def elige_finalizar(context):
    context["response"] = run_async(
        _finalizar(context["evaluacion"]["id"], context["estudiante_headers"])
    )


@when("el Estudiante entra a la revisión")
def entra_a_la_revision(context):
    context["revision"] = run_async(
        _obtener_revision(context["evaluacion"]["id"], context["estudiante_headers"])
    ).json()


@when("entra al listado de actividades y elige esa tarjeta")
def entra_al_listado_y_elige_tarjeta(context):
    context["response"] = run_async(
        _obtener_revision(context["evaluacion"]["id"], context["estudiante_headers"])
    )


@then("el sistema finaliza la Evaluacion")
def valida_finaliza_evaluacion(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["estado"] == "Finalizada"


@then("navega a la pantalla de revisión")
def valida_navega_a_revision(context):
    revision = run_async(
        _obtener_revision(context["evaluacion"]["id"], context["estudiante_headers"])
    )
    assert revision.status_code == 200


@then('ve el resumen "7 correctas, 3 incorrectas, 10 total"')
def valida_resumen_7_3_10(context):
    revision = context["revision"]
    assert revision["cantidad_correctas"] == 7
    assert revision["cantidad_incorrectas"] == 3
    assert revision["cantidad_preguntas"] == 10


@then("cada pregunta incorrecta muestra también la respuesta correcta")
def valida_incorrectas_muestran_respuesta_correcta(context):
    incorrectas = [fila for fila in context["revision"]["detalle"] if not fila["es_correcta"]]
    assert len(incorrectas) == 3
    for fila in incorrectas:
        assert fila["contenido_correcto"] is not None


@then("va directo a la revisión, sin pasar por la pantalla de rendir")
def valida_va_directo_a_revision(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["cantidad_preguntas"] == 1
