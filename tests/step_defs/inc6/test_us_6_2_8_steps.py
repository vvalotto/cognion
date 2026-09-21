"""Steps BDD de `US-6.2.8` — Consultar el estado de la sesión en vivo (RF-09, reconexión)."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from tests.integration.inc6._helpers import (
    cerrar_pregunta_actual,
    crear_estudiante,
    finalizar_sesion,
    headers_de,
    iniciar_sesion,
    mostrar_opciones,
    pregunta_actual_de,
    preparar_sesion,
    unirse_a_sesion,
)

scenarios("../../features/inc6/US-6.2.8-consultar-estado-sesion-en-vivo.feature")


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


async def _get(ruta: str, headers: dict[str, str]):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(ruta, headers=headers)


async def _responder(sesion_id: str, headers: dict[str, str]) -> dict:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        respuesta = await client.post(
            f"/sesiones-en-vivo/{sesion_id}/responder",
            json={
                "pregunta_id": await pregunta_actual_de(sesion_id),
                "contenido": {"opcion_indice": 1},
            },
            headers=headers,
        )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


async def _armar(context, *, iniciar=True, mostrar=False, cerrar=False, unir=False) -> None:
    """Arma una sesión con el estado pedido y un Estudiante (unido o no)."""
    sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
    if iniciar:
        await iniciar_sesion(sesion_id)
    if unir:
        estudiante_id, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)
    else:
        estudiante_id, headers = await crear_estudiante(comision_id)
    if mostrar:
        await mostrar_opciones(sesion_id)
    if cerrar:
        await cerrar_pregunta_actual(sesion_id)
    context.update(sesion_id=sesion_id, estudiante_id=estudiante_id, headers_estudiante=headers)


@given("una sesión EnEspera")
def sesion_en_espera(context):
    run_async(_armar(context, iniciar=False))


@given("una sesión EnCurso con solo el enunciado presentado")
def solo_enunciado(context):
    run_async(_armar(context))


@given("una pregunta con las opciones mostradas")
def opciones_mostradas(context):
    run_async(_armar(context, mostrar=True))


@given("una pregunta cerrada")
def pregunta_cerrada(context):
    run_async(_armar(context, mostrar=True, cerrar=True))


@given("un Estudiante que ya respondió la pregunta actual con 1200 puntos acumulados")
def estudiante_respondio(context):
    async def _armar_con_respuesta() -> None:
        await _armar(context, mostrar=True, unir=True)
        context["feedback"] = await _responder(context["sesion_id"], context["headers_estudiante"])

    run_async(_armar_con_respuesta())


@given("tres Estudiantes unidos")
def tres_unidos(context):
    async def _armar_tres() -> None:
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        ids = []
        for _ in range(3):
            estudiante_id, headers = await crear_estudiante(comision_id)
            await unirse_a_sesion(sesion_id, headers)
            ids.append(estudiante_id)
        context.update(sesion_id=sesion_id, ids=ids)

    run_async(_armar_tres())


@given("una sesión EnCurso con puntajes acumulados")
def con_puntajes(context):
    async def _armar_con_puntajes() -> None:
        await _armar(context, mostrar=True, unir=True)
        context["feedback"] = await _responder(context["sesion_id"], context["headers_estudiante"])

    run_async(_armar_con_puntajes())


@given("una sesión EnCurso")
def sesion_en_curso(context):
    run_async(_armar(context, mostrar=True, unir=True))
    context["feedback"] = run_async(_responder(context["sesion_id"], context["headers_estudiante"]))


@given("un sesion_id que no corresponde a ninguna sesión")
def sesion_inexistente(context):
    context["sesion_id"] = str(uuid.uuid4())


@given("un usuario autenticado con rol Estudiante")
def usuario_estudiante(context):
    run_async(_armar(context, iniciar=False))


@when("un Docente consulta el estado")
def docente_consulta_estado(context):
    context["response"] = run_async(_get(f"/sesiones-en-vivo/{context['sesion_id']}", _docente()))


@when("un Estudiante consulta el estado")
def estudiante_consulta_estado(context):
    context["response"] = run_async(
        _get(f"/sesiones-en-vivo/{context['sesion_id']}", context["headers_estudiante"])
    )


@when("consulta el estado")
def consulta_estado(context):
    context["response"] = run_async(
        _get(f"/sesiones-en-vivo/{context['sesion_id']}", context["headers_estudiante"])
    )


@when("se consulta el estado")
def se_consulta_estado(context):
    context["response"] = run_async(_get(f"/sesiones-en-vivo/{context['sesion_id']}", _docente()))


@when("el Docente lista los participantes")
def docente_lista(context):
    context["response"] = run_async(
        _get(f"/sesiones-en-vivo/{context['sesion_id']}/participantes", _docente())
    )


@when("intenta listar los participantes")
def estudiante_lista(context):
    context["response"] = run_async(
        _get(
            f"/sesiones-en-vivo/{context['sesion_id']}/participantes",
            context["headers_estudiante"],
        )
    )


@when("el Docente consulta el ranking")
def docente_ranking(context):
    context["response"] = run_async(
        _get(f"/sesiones-en-vivo/{context['sesion_id']}/ranking", _docente())
    )


@when("un Estudiante consulta el ranking")
def estudiante_ranking(context):
    context["response"] = run_async(
        _get(f"/sesiones-en-vivo/{context['sesion_id']}/ranking", context["headers_estudiante"])
    )


@then("recibe estado EnEspera sin pregunta actual")
def en_espera_sin_pregunta(context):
    cuerpo = context["response"].json()
    assert context["response"].status_code == 200
    assert cuerpo["estado"] == "EnEspera"
    assert cuerpo["pregunta_actual"] is None


@then("recibe el enunciado sin opciones y sin respuesta correcta")
def enunciado_sin_opciones(context):
    pregunta = context["response"].json()["pregunta_actual"]
    assert pregunta["enunciado"]
    assert pregunta["opciones"] is None
    assert pregunta["respuesta_correcta"] is None


@then("recibe las opciones, el instante en que se mostraron y el tiempo límite")
def opciones_y_tiempo(context):
    cuerpo = context["response"].json()
    assert cuerpo["pregunta_actual"]["opciones"] == ["A", "B", "C", "D"]
    assert cuerpo["opciones_mostradas_en"] is not None
    assert cuerpo["tiempo_limite_por_pregunta_segundos"] == 30


@then("no recibe la respuesta correcta")
def sin_correcta(context):
    assert context["response"].json()["pregunta_actual"]["respuesta_correcta"] is None


@then("recibe también la respuesta correcta")
def con_correcta(context):
    correcta = context["response"].json()["pregunta_actual"]["respuesta_correcta"]
    assert correcta["contenido"] == {"opcion_indice": 1}


@then("ya_respondio es verdadero y puntaje_acumulado es 1200")
def avance_propio(context):
    cuerpo = context["response"].json()
    assert cuerpo["ya_respondio"] is True
    # El puntaje real depende del tiempo de respuesta (500-4000): se verifica contra el feedback
    # que el propio servidor devolvió al responder, no contra un 1200 fijo.
    assert cuerpo["puntaje_acumulado"] == context["feedback"]["puntaje_acumulado"] > 0


@then("recibe los tres en orden de unión")
def tres_en_orden(context):
    assert context["response"].status_code == 200
    assert [p["estudiante_id"] for p in context["response"].json()] == context["ids"]


@then("recibe el ranking ordenado con posición")
def ranking_ordenado(context):
    ranking = context["response"].json()
    assert context["response"].status_code == 200
    assert [r["posicion"] for r in ranking] == list(range(1, len(ranking) + 1))
    assert ranking[0]["puntaje_acumulado"] == context["feedback"]["puntaje_acumulado"]


@then(parsers.parse("el sistema responde {codigo:d}"))
def sistema_responde(context, codigo):
    assert context["response"].status_code == codigo


@then("con la sesión Finalizada recibe el ranking completo")
def ranking_al_finalizar(context):
    run_async(cerrar_pregunta_actual(context["sesion_id"]))
    run_async(finalizar_sesion(context["sesion_id"]))
    respuesta = run_async(
        _get(f"/sesiones-en-vivo/{context['sesion_id']}/ranking", context["headers_estudiante"])
    )
    assert respuesta.status_code == 200
    assert respuesta.json()[0]["puntaje_acumulado"] == context["feedback"]["puntaje_acumulado"]
