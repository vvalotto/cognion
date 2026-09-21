"""Steps BDD de `US-6.2.6` — Docente avanza a la siguiente pregunta (RF-09)."""

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
    finalizar_sesion,
    headers_de,
    iniciar_sesion,
    mostrar_opciones,
    preparar_sesion,
)

scenarios("../../features/inc6/US-6.2.6-avanzar-siguiente-pregunta.feature")


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


@given("una sesión en la pregunta 1 de 5, ya cerrada")
def pregunta_1_cerrada(context):
    run_async(_armar(context, avances=0))


@given("una sesión en la pregunta 4 de 5, ya cerrada")
def pregunta_4_cerrada(context):
    run_async(_armar(context, avances=3))


@given("una sesión en la última pregunta, ya cerrada")
def ultima_cerrada(context):
    run_async(_armar(context, avances=4))


@given("una pregunta con las opciones mostradas y sin cerrar")
def opciones_sin_cerrar(context):
    run_async(_armar(context, avances=0, cerrar=False))


@given("una sesión EnEspera o Finalizada")
def sesion_en_espera_o_finalizada(context):
    async def _armar_ambas() -> list[str]:
        en_espera, _ = await preparar_sesion()
        finalizada, _ = await preparar_sesion()
        await iniciar_sesion(finalizada)
        await mostrar_opciones(finalizada)
        await _post(finalizada, "cerrar-pregunta", _docente())
        await finalizar_sesion(finalizada)
        return [en_espera, finalizada]

    context["sesiones"] = run_async(_armar_ambas())


@given("un sesion_id que no corresponde a ninguna sesión")
def sesion_inexistente(context):
    context["sesion_id"] = str(uuid.uuid4())


@given("un usuario autenticado con rol Estudiante")
def usuario_estudiante(context):
    run_async(_armar(context, avances=0))


@when("el Docente avanza")
def docente_avanza_con_conectados(context):
    """Avanza con el Docente y un Estudiante conectados al canal, para verificar el broadcast."""
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
                f"/sesiones-en-vivo/{sesion_id}/avanzar", headers=docente
            )
            if context["response"].status_code == 200:
                context["mensajes"] = [ws.receive_json() for ws in conectados]
        finally:
            for ws in sockets:
                ws.__exit__(None, None, None)


@when("el Docente intenta avanzar")
def docente_intenta_avanzar(context):
    ids = context.get("sesiones") or [context["sesion_id"]]
    context["responses"] = [run_async(_post(i, "avanzar", _docente())) for i in ids]
    context["response"] = context["responses"][0]


@when("intenta avanzar")
def estudiante_intenta_avanzar(context):
    context["response"] = run_async(
        _post(context["sesion_id"], "avanzar", context["headers_estudiante"])
    )


@then("pregunta_actual_indice pasa a 1 con las opciones ocultas y la pregunta sin cerrar")
def avance_persistido(context):
    assert context["response"].status_code == 200
    sesion, eventos = run_async(_reconstruir(context["sesion_id"]))
    assert eventos[-1].event_type == "SiguientePreguntaPresentada"
    assert sesion.pregunta_actual_indice == 1
    assert sesion.opciones_mostradas is False
    assert sesion.pregunta_actual_cerrada is False


@then("todos los conectados reciben el enunciado de la pregunta 2, sin opciones")
def todos_reciben_el_enunciado(context):
    assert len(context["mensajes"]) == 2  # Docente y Estudiante
    assert context["mensajes"][0] == context["mensajes"][1]
    mensaje = context["mensajes"][0]
    assert mensaje["tipo"] == "pregunta_presentada"
    assert mensaje["pregunta_actual_indice"] == 1
    assert set(mensaje["pregunta"]) == {"pregunta_id", "enunciado", "tipo"}


@then("queda en la pregunta 5")
def queda_en_la_5(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["pregunta_actual_indice"] == 4


@then(parsers.parse("el sistema rechaza con PreguntaActualNoCerrada ({codigo:d})"))
def rechazo_no_cerrada(context, codigo):
    assert context["response"].status_code == codigo
    assert "cerrada" in context["response"].json()["detail"]


@then(parsers.parse("el sistema rechaza con NoQuedanPreguntas ({codigo:d})"))
def rechazo_no_quedan(context, codigo):
    assert context["response"].status_code == codigo
    assert "más preguntas" in context["response"].json()["detail"]


@then(parsers.parse("el sistema rechaza con SesionNoEnCurso ({codigo:d})"))
def rechazo_no_en_curso(context, codigo):
    assert all(r.status_code == codigo for r in context["responses"])
    assert all("no está en curso" in r.json()["detail"] for r in context["responses"])


@then(parsers.parse("el sistema rechaza con SesionNoExiste ({codigo:d})"))
def rechazo_inexistente(context, codigo):
    assert context["response"].status_code == codigo


@then(parsers.parse("el sistema responde {codigo:d}"))
def sistema_responde(context, codigo):
    assert context["response"].status_code == codigo
