"""Steps BDD de `US-6.2.2` — Docente muestra las opciones de la pregunta actual (RF-09)."""

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
    preparar_sesion,
)

scenarios("../../features/inc6/US-6.2.2-mostrar-opciones-en-vivo.feature")


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


async def _post_mostrar(sesion_id: str, headers: dict[str, str]):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(f"/sesiones-en-vivo/{sesion_id}/mostrar-opciones", headers=headers)


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


def _preparar_en_curso(context, opcion_multiple: bool) -> None:
    context["sesion_id"], comision_id = run_async(preparar_sesion(opcion_multiple=opcion_multiple))
    run_async(iniciar_sesion(context["sesion_id"]))
    _, context["headers_estudiante"] = run_async(crear_estudiante(comision_id))


@given("una sesión EnCurso con el enunciado de la primera pregunta presentado")
def sesion_en_curso_opcion_multiple(context):
    _preparar_en_curso(context, opcion_multiple=True)


@given("una sesión EnCurso cuya pregunta actual es de Verdadero/Falso")
def sesion_en_curso_verdadero_falso(context):
    _preparar_en_curso(context, opcion_multiple=False)


@given("una pregunta con las opciones ya mostradas")
def opciones_ya_mostradas(context):
    _preparar_en_curso(context, opcion_multiple=True)
    assert run_async(_post_mostrar(context["sesion_id"], _docente())).status_code == 200


@given("una sesión en estado EnEspera")
def sesion_en_espera(context):
    context["sesion_id"], _ = run_async(preparar_sesion())


@given("un sesion_id que no corresponde a ninguna sesión")
def sesion_inexistente(context):
    context["sesion_id"] = str(uuid.uuid4())


@given("un usuario autenticado con rol Estudiante")
def usuario_estudiante(context):
    _preparar_en_curso(context, opcion_multiple=True)


@when("el Docente muestra las opciones")
def docente_muestra(context):
    """Muestra con el Docente y el Estudiante conectados al canal, para verificar el broadcast."""
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
                f"/sesiones-en-vivo/{sesion_id}/mostrar-opciones", headers=docente
            )
            if context["response"].status_code == 200:
                context["mensajes"] = [ws.receive_json() for ws in conectados]
        finally:
            for ws in sockets:
                ws.__exit__(None, None, None)


@when("el Docente intenta mostrarlas de nuevo")
@when("el Docente intenta mostrar las opciones")
def docente_intenta_mostrar(context):
    context["response"] = run_async(_post_mostrar(context["sesion_id"], _docente()))


@when("intenta mostrar las opciones")
def estudiante_intenta_mostrar(context):
    context["response"] = run_async(
        _post_mostrar(context["sesion_id"], context["headers_estudiante"])
    )


@then("opciones_mostradas pasa a verdadero y queda registrado el instante")
def opciones_registradas(context):
    eventos = run_async(_eventos_de_sesion(context["sesion_id"]))
    assert eventos[-1].event_type == "OpcionesEnVivoMostradas"
    assert eventos[-1].payload["ocurrido_en"]
    assert eventos[-1].payload["opciones"] == ["A", "B", "C", "D"]


@then("todos los conectados reciben las opciones sin indicar la correcta")
def todos_reciben_opciones(context):
    assert len(context["mensajes"]) == 2  # Docente y Estudiante
    for mensaje in context["mensajes"]:
        assert mensaje["tipo"] == "opciones_mostradas"
        assert mensaje["opciones"] == ["A", "B", "C", "D"]
        assert mensaje["cantidad_respuestas"] == 0
        assert "es_correcta" not in str(mensaje)
        assert "correcta" not in mensaje


@then("la respuesta HTTP es 200")
def http_200(context):
    assert context["response"].status_code == 200


@then("el mensaje indica el tipo de pregunta y no trae lista de opciones")
def mensaje_verdadero_falso(context):
    for mensaje in context["mensajes"]:
        assert mensaje["tipo"] == "opciones_mostradas"
        assert mensaje["opciones"] is None


@then(
    parsers.parse(
        "el sistema rechaza con OpcionesYaMostradas ({codigo:d}) sin emitir un evento nuevo"
    )
)
def rechazo_ya_mostradas(context, codigo):
    assert context["response"].status_code == codigo
    assert "ya se mostraron" in context["response"].json()["detail"]
    assert len(run_async(_eventos_de_sesion(context["sesion_id"]))) == 3


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
