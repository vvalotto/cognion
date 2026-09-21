"""Steps BDD de `US-6.2.5` — Docente cierra la pregunta actual (RF-09)."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from tests.integration.inc6._helpers import (
    crear_estudiante,
    headers_de,
    iniciar_sesion,
    mostrar_opciones,
    pregunta_actual_de,
    preparar_sesion,
    unirse_a_sesion,
)

scenarios("../../features/inc6/US-6.2.5-cerrar-pregunta-en-vivo.feature")


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


async def _post_cerrar(sesion_id: str, headers: dict[str, str]):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(f"/sesiones-en-vivo/{sesion_id}/cerrar-pregunta", headers=headers)


async def _eventos_de_sesion(sesion_id: str) -> list:
    async with SessionLocal() as session:
        resultado = await session.execute(
            text(
                "SELECT event_type, payload FROM events WHERE aggregate_type = "
                "'ActividadEvaluativaEnVivo' AND aggregate_id = :id ORDER BY sequence_number"
            ),
            {"id": sesion_id},
        )
        return resultado.all()


async def _responder(sesion_id: str, headers: dict[str, str], contenido: dict) -> None:
    pregunta_id = await pregunta_actual_de(sesion_id)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        respuesta = await client.post(
            f"/sesiones-en-vivo/{sesion_id}/responder",
            json={"pregunta_id": pregunta_id, "contenido": contenido},
            headers=headers,
        )
    assert respuesta.status_code == 200, respuesta.text


async def _armar(context, contenidos: list[dict | None], mostrar: bool = True) -> None:
    """Sesión en curso con un Estudiante unido por cada elemento de `contenidos`.

    Los Estudiantes se crean y unen **antes** de mostrar las opciones (bcrypt es lento y correría
    el temporizador). `None` deja al Estudiante sin responder.
    """
    sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
    await iniciar_sesion(sesion_id)
    estudiantes = []
    for _ in contenidos:
        estudiante_id, headers = await crear_estudiante(comision_id)
        await unirse_a_sesion(sesion_id, headers)
        estudiantes.append((estudiante_id, headers))
    context.update(sesion_id=sesion_id, estudiantes=[e for e, _ in estudiantes])
    context["headers_estudiante"] = (
        estudiantes[0][1] if estudiantes else (await crear_estudiante(comision_id))[1]
    )
    if mostrar:
        await mostrar_opciones(sesion_id)
    for (_, headers), contenido in zip(estudiantes, contenidos, strict=True):
        if contenido is not None:
            await _responder(sesion_id, headers, contenido)


def _preparar(context, contenidos: list[dict | None], mostrar: bool = True) -> None:
    run_async(_armar(context, contenidos, mostrar))


@given("una pregunta con las opciones mostradas y varios Estudiantes que respondieron")
def varios_respondieron(context):
    _preparar(context, [{"opcion_indice": 1}, {"opcion_indice": 0}])


@given("tres Estudiantes con distintos puntajes acumulados")
def tres_con_distintos_puntajes(context):
    _preparar(context, [{"opcion_indice": 1}, {"opcion_indice": 0}, None])


@given(parsers.parse('{a:d} respuestas a la opción "{x}" y {b:d} a la opción "{y}"'))
def respuestas_por_opcion(context, a, b, x, y):
    _preparar(
        context,
        [{"opcion_indice": int(x)}] * a + [{"opcion_indice": int(y)}] * b,
    )


@given("una pregunta con las opciones mostradas y ninguna respuesta")
def sin_respuestas(context):
    _preparar(context, [None, None])


@given("una pregunta con solo el enunciado presentado")
def solo_enunciado(context):
    _preparar(context, [None], mostrar=False)


@given("una pregunta ya cerrada")
def pregunta_ya_cerrada(context):
    _preparar(context, [None])
    assert run_async(_post_cerrar(context["sesion_id"], _docente())).status_code == 200


@given("una sesión EnEspera")
def sesion_en_espera(context):
    context["sesion_id"], _ = run_async(preparar_sesion())


@given("un sesion_id que no corresponde a ninguna sesión")
def sesion_inexistente(context):
    context["sesion_id"] = str(uuid.uuid4())


@given("un usuario autenticado con rol Estudiante")
def usuario_estudiante(context):
    _preparar(context, [None])


@when("el Docente la cierra")
@when("el Docente cierra la pregunta")
def docente_cierra_con_conectados(context):
    """Cierra con el Docente y un Estudiante conectados al canal, para verificar el broadcast."""
    docente = _docente()
    sesion_id = context["sesion_id"]
    tokens = [
        docente["Authorization"].split()[1],
        context["headers_estudiante"]["Authorization"].split()[1],
    ]
    with TestClient(app) as client:
        sockets = [
            client.websocket_connect(f"/sesiones-en-vivo/{sesion_id}/canal?token={token}")
            for token in tokens
        ]
        conectados = [ws.__enter__() for ws in sockets]
        try:
            context["response"] = client.post(
                f"/sesiones-en-vivo/{sesion_id}/cerrar-pregunta", headers=docente
            )
            if context["response"].status_code == 200:
                context["mensajes"] = [ws.receive_json() for ws in conectados]
        finally:
            for ws in sockets:
                ws.__exit__(None, None, None)


@when("el Docente intenta cerrarla")
@when("el Docente intenta cerrarla de nuevo")
@when("el Docente intenta cerrar la pregunta")
def docente_intenta_cerrar(context):
    context["response"] = run_async(_post_cerrar(context["sesion_id"], _docente()))


@when("intenta cerrar la pregunta")
def estudiante_intenta_cerrar(context):
    context["response"] = run_async(
        _post_cerrar(context["sesion_id"], context["headers_estudiante"])
    )


@then("pregunta_actual_cerrada pasa a verdadero y se persiste PreguntaEnVivoCerrada")
def cierre_persistido(context):
    eventos = run_async(_eventos_de_sesion(context["sesion_id"]))
    assert eventos[-1].event_type == "PreguntaEnVivoCerrada"
    assert eventos[-1].payload["pregunta_actual_indice"] == 0


@then(
    "todos los conectados reciben un único mensaje con la respuesta correcta, el histograma "
    "y el ranking"
)
def todos_reciben_el_cierre(context):
    assert len(context["mensajes"]) == 2  # Docente y Estudiante
    assert context["mensajes"][0] == context["mensajes"][1]
    mensaje = context["mensajes"][0]
    assert mensaje["tipo"] == "pregunta_cerrada"
    assert mensaje["respuesta_correcta"]["contenido"] == {"opcion_indice": 1}
    assert {d["opcion"] for d in mensaje["distribucion"]} == {"0", "1"}
    assert len(mensaje["ranking"]) == 2


@then("la respuesta HTTP es 200")
def http_200(context):
    assert context["response"].status_code == 200


@then("el ranking viene ordenado por puntaje descendente con su posición")
def ranking_ordenado(context):
    ranking = context["mensajes"][0]["ranking"]
    assert [f["posicion"] for f in ranking] == [1, 2, 3]
    puntajes = [f["puntaje_acumulado"] for f in ranking]
    assert puntajes == sorted(puntajes, reverse=True)
    assert puntajes[0] > 0 and puntajes[-1] == 0


@then(parsers.parse('la distribución informa {a:d} para "{x}" y {b:d} para "{y}"'))
def distribucion_por_opcion(context, a, b, x, y):
    distribucion = {d["opcion"]: d["cantidad"] for d in context["mensajes"][0]["distribucion"]}
    assert distribucion == {x: a, y: b}


@then("se acepta, con distribución vacía y el ranking con todos en su puntaje actual")
def cierre_sin_respuestas(context):
    assert context["response"].status_code == 200
    mensaje = context["mensajes"][0]
    assert mensaje["distribucion"] == []
    assert {f["estudiante_id"] for f in mensaje["ranking"]} == set(context["estudiantes"])
    assert all(f["puntaje_acumulado"] == 0 for f in mensaje["ranking"])


@then(parsers.parse("el sistema rechaza con OpcionesNoMostradasTodavia ({codigo:d})"))
def rechazo_opciones_no_mostradas(context, codigo):
    assert context["response"].status_code == codigo
    assert "opciones" in context["response"].json()["detail"]


@then(parsers.parse("el sistema rechaza con PreguntaYaCerrada ({codigo:d}) sin emitir otro evento"))
def rechazo_ya_cerrada(context, codigo):
    assert context["response"].status_code == codigo
    assert len(run_async(_eventos_de_sesion(context["sesion_id"]))) == 4


@then(parsers.parse("el sistema rechaza con SesionNoEnCurso ({codigo:d})"))
def rechazo_no_en_curso(context, codigo):
    assert context["response"].status_code == codigo
    assert "no está en curso" in context["response"].json()["detail"]


@then(parsers.parse("el sistema rechaza con SesionNoExiste ({codigo:d})"))
def rechazo_inexistente(context, codigo):
    assert context["response"].status_code == codigo


@then(parsers.parse("el sistema responde {codigo:d}"))
def sistema_responde(context, codigo):
    assert context["response"].status_code == codigo
