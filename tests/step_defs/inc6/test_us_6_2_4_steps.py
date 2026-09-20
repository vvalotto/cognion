"""Steps BDD de `US-6.2.4` — Estudiante responde una pregunta en vivo (RF-09, RF-10)."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
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
    sembrar_opciones_mostradas_hace,
    unirse_a_sesion,
)

scenarios("../../features/inc6/US-6.2.4-responder-pregunta-en-vivo.feature")

CORRECTA = {"opcion_indice": 1}
INCORRECTA = {"opcion_indice": 0}


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.execute(text("DELETE FROM ranking_por_sesion"))
        await session.execute(text("DELETE FROM distribucion_por_pregunta"))
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


async def _preparar(context, *, mostrar: str | None = "ahora", unirse: bool = True) -> None:
    """Sesión iniciada (opción múltiple, "B" correcta) con un Estudiante y opciones según `mostrar`.

    `mostrar`: `"ahora"`, `"viejo"` (fuera del tiempo límite) o `None` (solo el enunciado).
    """
    sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
    await iniciar_sesion(sesion_id)
    estudiante_id, headers = await crear_estudiante(comision_id)
    if unirse:
        await unirse_a_sesion(sesion_id, headers)
    if mostrar == "ahora":
        await mostrar_opciones(sesion_id)
    elif mostrar == "viejo":
        await sembrar_opciones_mostradas_hace(sesion_id, 300)
    context.update(
        sesion_id=sesion_id,
        estudiante_id=estudiante_id,
        headers=headers,
        pregunta_id=await pregunta_actual_de(sesion_id),
    )


async def _post(context, contenido, pregunta_id=None, headers=None):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(
            f"/sesiones-en-vivo/{context['sesion_id']}/responder",
            json={"pregunta_id": pregunta_id or context["pregunta_id"], "contenido": contenido},
            headers=headers or context["headers"],
        )


def _responder_con_canal(context, contenido) -> None:
    """Responde con el Docente y el Estudiante conectados al canal, para verificar el broadcast."""
    docente = headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)
    tokens = [
        docente["Authorization"].split()[1],
        context["headers"]["Authorization"].split()[1],
    ]
    sesion_id = context["sesion_id"]
    with TestClient(app) as client:
        sockets = [
            client.websocket_connect(f"/sesiones-en-vivo/{sesion_id}/canal?token={token}")
            for token in tokens
        ]
        conectados = [ws.__enter__() for ws in sockets]
        try:
            context["response"] = client.post(
                f"/sesiones-en-vivo/{sesion_id}/responder",
                json={"pregunta_id": context["pregunta_id"], "contenido": contenido},
                headers=context["headers"],
            )
            if context["response"].status_code == 200:
                context["mensajes"] = [ws.receive_json() for ws in conectados]
        finally:
            for ws in sockets:
                ws.__exit__(None, None, None)


async def _eventos_participacion(context) -> list:
    async with SessionLocal() as session:
        resultado = await session.execute(
            text(
                "SELECT event_type, payload FROM events WHERE aggregate_type = 'ParticipacionEnVivo' "
                "AND payload->>'sesion_id' = :s AND payload->>'estudiante_id' = :e "
                "ORDER BY sequence_number"
            ),
            {"s": context["sesion_id"], "e": context["estudiante_id"]},
        )
        return resultado.all()


async def _consultar(sql: str, **params):
    async with SessionLocal() as session:
        return (await session.execute(text(sql), params)).all()


@given("una pregunta con las opciones mostradas y un Estudiante unido")
@given("una pregunta con las opciones mostradas")
@given("un Estudiante que responde una pregunta")
def opciones_mostradas_con_estudiante(context):
    run_async(_preparar(context))


@given("un Estudiante que ya respondió la pregunta actual")
def estudiante_ya_respondio(context):
    run_async(_preparar(context))
    primera = run_async(_post(context, CORRECTA))
    assert primera.status_code == 200
    context["puntaje_previo"] = primera.json()["puntaje_acumulado"]


@given("una pregunta cuyas opciones se mostraron hace más del tiempo límite")
def opciones_vencidas(context):
    run_async(_preparar(context, mostrar="viejo"))


@given("una pregunta con solo el enunciado presentado")
def solo_enunciado(context):
    run_async(_preparar(context, mostrar=None))


@given("una pregunta cerrada por el Docente")
def pregunta_cerrada(context):
    run_async(_preparar(context))

    async def _cerrar():
        async with SessionLocal() as session:
            store = SQLAlchemyEventStore(session)
            eventos = await store.load("ActividadEvaluativaEnVivo", uuid.UUID(context["sesion_id"]))
            await store.append(
                "ActividadEvaluativaEnVivo",
                uuid.UUID(context["sesion_id"]),
                len(eventos),
                [EventoParaAlmacenar("PreguntaEnVivoCerrada", {"sesion_id": context["sesion_id"]})],
            )

    run_async(_cerrar())


@given("una sesión en la pregunta 2")
def sesion_en_la_pregunta_2(context):
    # `AvanzarSiguientePregunta` es US-6.2.6: todavía no hay forma de llegar a la pregunta 2. Se
    # prepara la sesión en su pregunta actual y el `When` responde con el id de otra pregunta.
    run_async(_preparar(context))

    async def _otra_pregunta() -> str:
        async with SessionLocal() as session:
            eventos = await SQLAlchemyEventStore(session).load(
                "ActividadEvaluativaEnVivo", uuid.UUID(context["sesion_id"])
            )
        return eventos[0].payload["preguntas"][1]["pregunta_id"]

    context["otra_pregunta_id"] = run_async(_otra_pregunta())


@given("un Estudiante que nunca se unió a la sesión")
def estudiante_sin_unirse(context):
    run_async(_preparar(context, unirse=False))


@given("dos envíos simultáneos de la misma respuesta del mismo Estudiante")
def dos_envios(context):
    run_async(_preparar(context))


@given("un usuario autenticado con rol Docente")
def usuario_docente(context):
    run_async(_preparar(context))
    context["headers"] = headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)


@when("el Estudiante elige la opción correcta dentro del tiempo límite")
def elige_correcta(context):
    _responder_con_canal(context, CORRECTA)


@when("el Estudiante elige una opción incorrecta")
def elige_incorrecta(context):
    context["response"] = run_async(_post(context, INCORRECTA))


@when("se registra la respuesta")
def se_registra(context):
    context["response"] = run_async(_post(context, CORRECTA))


@when("intenta responderla de nuevo")
def responde_de_nuevo(context):
    context["response"] = run_async(_post(context, INCORRECTA))


@when("el Estudiante intenta responder")
@when("intenta responder")
def intenta_responder(context):
    context["response"] = run_async(_post(context, CORRECTA))


@when("el Estudiante responde con el pregunta_id de la pregunta 1")
def responde_otra_pregunta(context):
    context["response"] = run_async(
        _post(context, CORRECTA, pregunta_id=context["otra_pregunta_id"])
    )


@when("se procesan")
def se_procesan(context):
    async def _dos():
        return await asyncio.gather(_post(context, CORRECTA), _post(context, CORRECTA))

    context["respuestas"] = run_async(_dos())


@then("se registra la respuesta con tiempo_respuesta medido por el servidor")
def registrada_con_tiempo(context):
    eventos = run_async(_eventos_participacion(context))
    assert eventos[-1].event_type == "RespuestaEnVivoRegistrada"
    assert eventos[-1].payload["tiempo_respuesta_segundos"] >= 0


@then("la respuesta HTTP trae es_correcta=true, el puntaje de esa pregunta y el puntaje acumulado")
def feedback_correcto(context):
    assert context["response"].status_code == 200
    cuerpo = context["response"].json()
    assert cuerpo["es_correcta"] is True
    assert 1500 <= cuerpo["puntaje"] <= 3000  # dificultad media × importancia alta
    assert cuerpo["puntaje_acumulado"] == cuerpo["puntaje"]


@then("todos los conectados reciben el conteo actualizado de respuestas, sin desglose por opción")
def conteo_a_todos(context):
    assert len(context["mensajes"]) == 2  # Docente y Estudiante
    for mensaje in context["mensajes"]:
        assert mensaje == {
            "tipo": "conteo_respuestas_actualizado",
            "pregunta_actual_indice": 0,
            "cantidad_respuestas": 1,
        }


@then("se registra la respuesta con puntaje 0 y es_correcta=false")
def registrada_incorrecta(context):
    assert context["response"].json() == {
        "es_correcta": False,
        "puntaje": 0,
        "puntaje_acumulado": 0,
    }
    eventos = run_async(_eventos_participacion(context))
    assert eventos[-1].payload["es_correcta"] is False
    assert eventos[-1].payload["puntaje"] == 0


@then("su puntaje acumulado en el ranking y el histograma de esa opción reflejan la respuesta")
def proyecciones_reflejan(context):
    acumulado = context["response"].json()["puntaje_acumulado"]
    ranking = run_async(
        _consultar(
            "SELECT puntaje_acumulado FROM ranking_por_sesion WHERE sesion_id = :s "
            "AND estudiante_id = :e",
            s=context["sesion_id"],
            e=context["estudiante_id"],
        )
    )
    assert ranking[0].puntaje_acumulado == acumulado
    histograma = run_async(
        _consultar(
            "SELECT opcion, cantidad FROM distribucion_por_pregunta WHERE sesion_id = :s "
            "AND pregunta_id = :p",
            s=context["sesion_id"],
            p=context["pregunta_id"],
        )
    )
    assert [(f.opcion, f.cantidad) for f in histograma] == [("1", 1)]


@then(
    parsers.parse(
        "el sistema rechaza con RespuestaYaRegistrada ({codigo:d}) y no cambia su puntaje"
    )
)
def rechazo_ya_registrada(context, codigo):
    assert context["response"].status_code == codigo
    assert "Ya registraste" in context["response"].json()["detail"]
    ranking = run_async(
        _consultar(
            "SELECT puntaje_acumulado FROM ranking_por_sesion WHERE estudiante_id = :e",
            e=context["estudiante_id"],
        )
    )
    assert ranking[0].puntaje_acumulado == context["puntaje_previo"]


@then(parsers.parse("el sistema rechaza con TiempoAgotado ({codigo:d})"))
def rechazo_tiempo(context, codigo):
    assert context["response"].status_code == codigo
    assert "fuera del tiempo límite" in context["response"].json()["detail"]


@then(parsers.parse("el sistema rechaza con OpcionesNoMostradasTodavia ({codigo:d})"))
def rechazo_opciones_no_mostradas(context, codigo):
    assert context["response"].status_code == codigo
    assert "todavía no se mostraron" in context["response"].json()["detail"]


@then(parsers.parse("el sistema rechaza con PreguntaYaCerrada ({codigo:d})"))
def rechazo_cerrada(context, codigo):
    assert context["response"].status_code == codigo
    assert "ya fue cerrada" in context["response"].json()["detail"]


@then(parsers.parse("el sistema rechaza con PreguntaNoActual ({codigo:d})"))
def rechazo_no_actual(context, codigo):
    assert context["response"].status_code == codigo
    assert "no es la pregunta actual" in context["response"].json()["detail"]


@then(parsers.parse("el sistema rechaza con ParticipacionNoExiste ({codigo:d})"))
def rechazo_sin_participacion(context, codigo):
    assert context["response"].status_code == codigo
    assert "no se unió" in context["response"].json()["detail"]


@then(parsers.parse("uno se registra y el otro recibe RespuestaYaRegistrada ({codigo:d})"))
def uno_gana(context, codigo):
    assert sorted(r.status_code for r in context["respuestas"]) == [200, codigo]
    assert len(run_async(_eventos_participacion(context))) == 2  # EstudianteUnido + 1 respuesta


@then(parsers.parse("el sistema responde {codigo:d}"))
def responde_codigo(context, codigo):
    assert context["response"].status_code == codigo
