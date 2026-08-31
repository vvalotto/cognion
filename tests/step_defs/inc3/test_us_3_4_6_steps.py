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

scenarios("../../features/inc3/US-3.4.6-rendir-evaluacion.feature")


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


async def _crear_materia_con_preguntas(cantidad_verdadero_falso: int, con_opcion_multiple: bool) -> str:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        creada = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=docente_headers()
        )
        banco_id = creada.json()["banco_id"]

        for i in range(cantidad_verdadero_falso):
            await client.post(
                "/preguntas/verdadero-falso",
                json={
                    "banco_id": banco_id,
                    "texto": f"Pregunta VF {i} {uuid.uuid4()}",
                    "respuesta_correcta": True,
                    "unidad_tematica": "Unidad 1",
                    "tema": "Tema",
                    "dificultad": "medio",
                    "importancia": "alto",
                },
                headers=docente_headers(),
            )

        if con_opcion_multiple:
            await client.post(
                "/preguntas/opcion-multiple",
                json={
                    "banco_id": banco_id,
                    "texto": f"¿Cuál NO es un principio SOLID? {uuid.uuid4()}",
                    "opciones": [
                        {"texto": "Responsabilidad única", "es_correcta": False},
                        {"texto": "Herencia múltiple obligatoria", "es_correcta": True},
                    ],
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


async def _registrar_respuesta(evaluacion_id: str, pregunta_id: str, estudiante_headers: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            f"/evaluaciones/{evaluacion_id}/respuestas",
            json={"pregunta_id": pregunta_id, "contenido": {"valor": True}},
            headers=estudiante_headers,
        )


async def _suspender(evaluacion_id: str, estudiante_headers: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            f"/evaluaciones/{evaluacion_id}/suspender", headers=estudiante_headers
        )


async def _reanudar(evaluacion_id: str, estudiante_headers: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            f"/evaluaciones/{evaluacion_id}/reanudar", headers=estudiante_headers
        )


async def _armar_evaluacion_en_curso(cantidad_preguntas: int = 2):
    materia_id = await _crear_materia_con_preguntas(cantidad_preguntas, con_opcion_multiple=False)
    actividad_id = await _crear_actividad(materia_id, cantidad_preguntas)
    _estudiante_id, headers = await crear_estudiante()
    evaluacion = await _iniciar_evaluacion(actividad_id, headers)
    return evaluacion, headers


@given("un Estudiante en la pregunta actual de una Evaluacion EnCurso")
def estudiante_en_pregunta_actual(context):
    evaluacion, headers = run_async(_armar_evaluacion_en_curso())
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers
    context["pregunta_id"] = evaluacion["preguntas_asignadas"][0]["pregunta_id"]


@given("un Estudiante que ya confirmó 3 de 10 respuestas")
def estudiante_con_3_de_10_respondidas(context):
    evaluacion, headers = run_async(_armar_evaluacion_en_curso(cantidad_preguntas=10))
    ids_respondidos = [p["pregunta_id"] for p in evaluacion["preguntas_asignadas"][:3]]
    for pregunta_id in ids_respondidos:
        run_async(_registrar_respuesta(evaluacion["id"], pregunta_id, headers))
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers
    context["ids_respondidos"] = ids_respondidos


@given("un Estudiante en una Evaluacion EnCurso")
def estudiante_en_evaluacion_en_curso(context):
    evaluacion, headers = run_async(_armar_evaluacion_en_curso())
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers


@given("un Estudiante con una Evaluacion Suspendida")
def estudiante_con_evaluacion_suspendida(context):
    evaluacion, headers = run_async(_armar_evaluacion_en_curso())
    run_async(_suspender(evaluacion["id"], headers))
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers


@given("una pregunta asignada dentro de una Evaluacion EnCurso")
def pregunta_asignada_en_evaluacion_en_curso(context):
    materia_id = run_async(_crear_materia_con_preguntas(0, con_opcion_multiple=True))
    actividad_id = run_async(_crear_actividad(materia_id, 1))
    _estudiante_id, headers = run_async(crear_estudiante())
    evaluacion = run_async(_iniciar_evaluacion(actividad_id, headers))
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers
    context["pregunta_id"] = evaluacion["preguntas_asignadas"][0]["pregunta_id"]


@when("elige una opción y confirma")
def elige_opcion_y_confirma(context):
    context["response"] = run_async(
        _registrar_respuesta(
            context["evaluacion"]["id"], context["pregunta_id"], context["estudiante_headers"]
        )
    )


@when("recarga la página o vuelve a entrar más tarde")
def recarga_la_pagina(context):
    context["reconexion"] = run_async(
        _iniciar_evaluacion(context["evaluacion"]["actividad_id"], context["estudiante_headers"])
    )


@when('toca "Pausar y salir"')
def toca_pausar_y_salir(context):
    context["response"] = run_async(
        _suspender(context["evaluacion"]["id"], context["estudiante_headers"])
    )


@when('toca "Continuar" en la pantalla de evaluación suspendida')
def toca_continuar(context):
    context["response"] = run_async(
        _reanudar(context["evaluacion"]["id"], context["estudiante_headers"])
    )


@when("el Estudiante consulta el contenido de la pregunta actual")
def consulta_contenido_pregunta_actual(context):
    reconexion = run_async(
        _iniciar_evaluacion(context["evaluacion"]["actividad_id"], context["estudiante_headers"])
    )
    asignada = next(
        p
        for p in reconexion["preguntas_asignadas"]
        if p["pregunta_id"] == context["pregunta_id"]
    )
    context["asignada"] = asignada


@then("el sistema persiste la Respuesta de inmediato")
def valida_persistencia_inmediata(context):
    assert context["response"].status_code == 201


@then("avanza a la siguiente pregunta")
def valida_avanza_a_siguiente(context):
    reconexion = run_async(
        _iniciar_evaluacion(context["evaluacion"]["actividad_id"], context["estudiante_headers"])
    )
    assert context["pregunta_id"] in reconexion["preguntas_respondidas"]
    assert len(reconexion["preguntas_asignadas"]) > 1


@then("retoma en la misma Evaluacion, con las 3 respuestas ya marcadas como respondidas")
def valida_retoma_con_3_respondidas(context):
    reconexion = context["reconexion"]
    assert reconexion["id"] == context["evaluacion"]["id"]
    assert set(reconexion["preguntas_respondidas"]) == set(context["ids_respondidos"])


@then("no se genera un nuevo set de preguntas")
def valida_mismo_set(context):
    assert context["reconexion"]["preguntas_asignadas"] == context["evaluacion"]["preguntas_asignadas"]


@then("el sistema suspende la Evaluacion")
def valida_suspende_evaluacion(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["estado"] == "Suspendida"


@then("navega a la pantalla de evaluación suspendida")
def valida_navega_a_suspendida(context):
    reconexion = run_async(
        _iniciar_evaluacion(context["evaluacion"]["actividad_id"], context["estudiante_headers"])
    )
    assert reconexion["estado"] == "Suspendida"


@then("vuelve a rendir en el mismo punto donde quedó")
def valida_vuelve_a_rendir_en_el_mismo_punto(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["estado"] == "EnCurso"
    assert context["response"].json()["preguntas_asignadas"] == context["evaluacion"][
        "preguntas_asignadas"
    ]
    assert (
        context["response"].json()["preguntas_respondidas"]
        == context["evaluacion"]["preguntas_respondidas"]
    )


@then("ve el enunciado y las opciones")
def valida_ve_enunciado_y_opciones(context):
    asignada = context["asignada"]
    assert asignada["enunciado"]
    assert asignada["opciones"] is not None
    assert len(asignada["opciones"]) >= 2


@then("ninguna opción indica si es correcta")
def valida_ninguna_opcion_indica_correccion(context):
    for opcion in context["asignada"]["opciones"]:
        assert isinstance(opcion, str)
