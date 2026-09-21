"""Steps BDD de `US-6.2.7` — Docente finaliza la sesión en vivo (RF-09)."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
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
    iniciar_y_finalizar,
    mostrar_opciones,
    preparar_sesion,
)

scenarios("../../features/inc6/US-6.2.7-finalizar-sesion-en-vivo.feature")


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


async def _post(sesion_id: str, accion: str, headers: dict[str, str]):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(f"/sesiones-en-vivo/{sesion_id}/{accion}", headers=headers)


async def _reconstruir(sesion_id: str) -> tuple[ActividadEvaluativaEnVivo, list]:
    async with SessionLocal() as session:
        eventos = await SQLAlchemyEventStore(session).load(
            "ActividadEvaluativaEnVivo", uuid.UUID(sesion_id)
        )
    return ActividadEvaluativaEnVivo.reconstruir(eventos), eventos


async def _mostrar_y_cerrar(sesion_id: str) -> None:
    await mostrar_opciones(sesion_id)
    assert (await _post(sesion_id, "cerrar-pregunta", _docente())).status_code == 200


async def _armar(context, avances: int, cerrar: bool = True) -> None:
    """Sesión iniciada en la pregunta `avances + 1` de 5; cerrada si `cerrar`, si no con opciones."""
    sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
    await iniciar_sesion(sesion_id)
    _, headers_estudiante = await crear_estudiante(comision_id)
    context.update(sesion_id=sesion_id, headers_estudiante=headers_estudiante)
    for _ in range(avances):
        await _mostrar_y_cerrar(sesion_id)
        assert (await _post(sesion_id, "avanzar", _docente())).status_code == 200
    if cerrar:
        await _mostrar_y_cerrar(sesion_id)
    else:
        await mostrar_opciones(sesion_id)


@given("una sesión en la última pregunta, ya cerrada")
def ultima_cerrada(context):
    run_async(_armar(context, avances=4))


@given("una sesión en la pregunta 2 de 5, ya cerrada")
def pregunta_2_cerrada(context):
    run_async(_armar(context, avances=1))


@given("una pregunta actual sin cerrar")
def pregunta_sin_cerrar(context):
    run_async(_armar(context, avances=0, cerrar=False))


@given("una sesión EnEspera")
def sesion_en_espera(context):
    context["sesion_id"], comision_id = run_async(preparar_sesion())
    _, context["headers_estudiante"] = run_async(crear_estudiante(comision_id))


@given("una sesión Finalizada")
def sesion_finalizada(context):
    async def _armar_finalizada() -> None:
        sesion_id, comision_id = await preparar_sesion(opcion_multiple=True)
        await iniciar_y_finalizar(sesion_id)
        _, headers = await crear_estudiante(comision_id)
        context.update(sesion_id=sesion_id, headers_estudiante=headers)
        context["eventos_antes"] = len((await _reconstruir(sesion_id))[1])

    run_async(_armar_finalizada())


@given("un sesion_id que no corresponde a ninguna sesión")
def sesion_inexistente(context):
    context["sesion_id"] = str(uuid.uuid4())


@given("un usuario autenticado con rol Estudiante")
def usuario_estudiante(context):
    run_async(_armar(context, avances=0))


@when("el Docente finaliza la sesión")
def docente_finaliza_con_conectados(context):
    """Finaliza con el Docente y un Estudiante conectados al canal, para verificar el broadcast."""
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
                f"/sesiones-en-vivo/{sesion_id}/finalizar", headers=docente
            )
            if context["response"].status_code == 200:
                context["mensajes"] = [ws.receive_json() for ws in conectados]
        finally:
            for ws in sockets:
                ws.__exit__(None, None, None)


@when(
    parsers.re(r"el Docente intenta finalizar( de nuevo)?"),
)
def docente_intenta_finalizar(context):
    context["response"] = run_async(_post(context["sesion_id"], "finalizar", _docente()))


@when("un Estudiante intenta unirse")
def estudiante_intenta_unirse(context):
    context["response"] = run_async(
        _post(context["sesion_id"], "unirse", context["headers_estudiante"])
    )


@when("intenta finalizar la sesión")
def estudiante_intenta_finalizar(context):
    context["response"] = run_async(
        _post(context["sesion_id"], "finalizar", context["headers_estudiante"])
    )


@then("el estado pasa a Finalizada")
def estado_finalizada(context):
    assert context["response"].status_code == 200
    sesion, eventos = run_async(_reconstruir(context["sesion_id"]))
    assert eventos[-1].event_type == "SesionEnVivoFinalizada"
    assert sesion.estado == "Finalizada"


@then("todos los conectados reciben el ranking final ordenado por puntaje")
def todos_reciben_el_ranking(context):
    assert len(context["mensajes"]) == 2  # Docente y Estudiante
    assert context["mensajes"][0] == context["mensajes"][1]
    mensaje = context["mensajes"][0]
    assert mensaje["tipo"] == "sesion_finalizada"
    puntajes = [fila["puntaje_acumulado"] for fila in mensaje["ranking"]]
    assert puntajes == sorted(puntajes, reverse=True)


@then("se acepta y la sesión queda Finalizada")
def finalizacion_anticipada(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["estado"] == "Finalizada"
    assert context["response"].json()["pregunta_actual_indice"] == 1


@then(parsers.parse("el sistema rechaza con SesionYaFinalizada ({codigo:d})"))
def rechazo_ya_finalizada(context, codigo):
    assert context["response"].status_code == codigo
    assert "finalizada" in context["response"].json()["detail"]


@then(
    parsers.parse("el sistema rechaza con SesionYaFinalizada ({codigo:d}) sin emitir otro evento")
)
def rechazo_ya_finalizada_sin_evento(context, codigo):
    assert context["response"].status_code == codigo
    assert "finalizada" in context["response"].json()["detail"]
    _, eventos = run_async(_reconstruir(context["sesion_id"]))
    assert len(eventos) == context["eventos_antes"]


@then(parsers.parse("el sistema rechaza con PreguntaActualNoCerrada ({codigo:d})"))
def rechazo_no_cerrada(context, codigo):
    assert context["response"].status_code == codigo
    assert "cerrada" in context["response"].json()["detail"]


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
