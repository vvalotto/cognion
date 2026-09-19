"""Steps BDD de `US-6.1.4` — Docente inicia la sesión en vivo (RF-08)."""

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

scenarios("../../features/inc6/US-6.1.4-iniciar-sesion-en-vivo.feature")


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


async def _post_iniciar(sesion_id: str, headers: dict[str, str]):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(f"/sesiones-en-vivo/{sesion_id}/iniciar", headers=headers)


async def _post_unirse(sesion_id: str, headers: dict[str, str]):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(f"/sesiones-en-vivo/{sesion_id}/unirse", headers=headers)


async def _cantidad_de_eventos_de_sesion(sesion_id: str) -> int:
    async with SessionLocal() as session:
        resultado = await session.execute(
            text(
                "SELECT count(*) FROM events WHERE aggregate_type = 'ActividadEvaluativaEnVivo' "
                "AND aggregate_id = :id"
            ),
            {"id": sesion_id},
        )
        return resultado.scalar_one()


@given("una sesión en vivo en estado EnEspera con al menos un Estudiante unido")
def sesion_con_estudiante_unido(context):
    context["sesion_id"], comision_id = run_async(preparar_sesion())
    context["estudiante_id"], headers = run_async(crear_estudiante(comision_id))
    context["headers_estudiante"] = headers
    assert run_async(_post_unirse(context["sesion_id"], headers)).status_code == 200


@given("una sesión en vivo en estado EnEspera sin ningún Estudiante unido")
def sesion_sin_estudiantes(context):
    context["sesion_id"], _ = run_async(preparar_sesion())


@given("una sesión en vivo ya en estado EnCurso")
def sesion_en_curso(context):
    context["sesion_id"], _ = run_async(preparar_sesion())
    run_async(iniciar_sesion(context["sesion_id"]))


@given("un sesion_id que no corresponde a ninguna sesión en vivo")
def sesion_inexistente(context):
    context["sesion_id"] = str(uuid.uuid4())


@given("un usuario autenticado con rol Estudiante")
def usuario_estudiante(context):
    context["sesion_id"], comision_id = run_async(preparar_sesion())
    _, context["headers_estudiante"] = run_async(crear_estudiante(comision_id))


@when("el Docente la inicia")
def docente_inicia(context):
    """Inicia con el Docente y el Estudiante (si hay) conectados al canal, para el broadcast."""
    docente = _docente()
    sesion_id = context["sesion_id"]
    tokens = [docente["Authorization"].split()[1]]
    if "headers_estudiante" in context:
        tokens.append(context["headers_estudiante"]["Authorization"].split()[1])
    with TestClient(app) as client:
        sockets = [
            client.websocket_connect(f"/sesiones-en-vivo/{sesion_id}/canal?token={token}")
            for token in tokens
        ]
        conectados = [ws.__enter__() for ws in sockets]
        try:
            context["response"] = client.post(
                f"/sesiones-en-vivo/{sesion_id}/iniciar", headers=docente
            )
            if context["response"].status_code == 200:
                context["mensajes"] = [ws.receive_json() for ws in conectados]
        finally:
            for ws in sockets:
                ws.__exit__(None, None, None)


@when("el Docente intenta iniciarla de nuevo")
@when("el Docente intenta iniciarla")
def docente_intenta_iniciar(context):
    context["response"] = run_async(_post_iniciar(context["sesion_id"], _docente()))


@when("intenta iniciar una sesión en vivo")
def estudiante_intenta_iniciar(context):
    context["response"] = run_async(
        _post_iniciar(context["sesion_id"], context["headers_estudiante"])
    )


@then(parsers.parse("el estado pasa a EnCurso con pregunta_actual_indice={indice:d}"))
def estado_en_curso(context, indice):
    assert context["response"].status_code == 200
    body = context["response"].json()
    assert body["estado"] == "EnCurso"
    assert body["pregunta_actual_indice"] == indice
    assert run_async(_cantidad_de_eventos_de_sesion(context["sesion_id"])) == 2


@then("todos los conectados al canal reciben el enunciado de la primera pregunta, sin opciones")
def todos_reciben_enunciado(context):
    assert len(context["mensajes"]) == 2  # Docente y Estudiante
    for mensaje in context["mensajes"]:
        assert mensaje["tipo"] == "pregunta_presentada"
        assert mensaje["pregunta_actual_indice"] == 0
        assert mensaje["pregunta"]["enunciado"].startswith("Pregunta ")
        assert "opciones" not in mensaje["pregunta"]


@then("la operación se acepta igual — el dominio no exige un mínimo de participantes")
def aceptada_sin_participantes(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["estado"] == "EnCurso"


@then(parsers.parse("el sistema rechaza la operación con SesionYaIniciada ({codigo:d})"))
def rechazo_ya_iniciada(context, codigo):
    assert context["response"].status_code == codigo
    assert "iniciada" in context["response"].json()["detail"]
    assert run_async(_cantidad_de_eventos_de_sesion(context["sesion_id"])) == 2


@then(parsers.parse("el sistema rechaza la operación con SesionNoExiste ({codigo:d})"))
def rechazo_inexistente(context, codigo):
    assert context["response"].status_code == codigo


@then(parsers.parse("el sistema responde {codigo:d}"))
def sistema_responde(context, codigo):
    assert context["response"].status_code == codigo
