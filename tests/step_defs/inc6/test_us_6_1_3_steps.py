"""Steps BDD de `US-6.1.3` — Estudiante se une a una sesión en vivo (RF-08)."""

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
    preparar_sesion,
    sembrar_evento_de_sesion,
)

scenarios("../../features/inc6/US-6.1.3-unirse-sesion-en-vivo.feature")


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


async def _post_unirse(sesion_id: str, headers: dict[str, str]):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(f"/sesiones-en-vivo/{sesion_id}/unirse", headers=headers)


async def _eventos_de_participacion(sesion_id: str) -> list[dict]:
    async with SessionLocal() as session:
        resultado = await session.execute(
            text(
                "SELECT payload FROM events WHERE aggregate_type = 'ParticipacionEnVivo' "
                "AND payload->>'sesion_id' = :sid ORDER BY occurred_at"
            ),
            {"sid": sesion_id},
        )
        return [fila[0] for fila in resultado.all()]


def _preparar(context, *, sembrar: tuple[str, ...] = ()) -> None:
    """Crea la sesión (US-6.1.2) y un Estudiante de su Comisión; siembra estados posteriores."""
    context["sesion_id"], comision_id = run_async(preparar_sesion())
    for secuencia, tipo in enumerate(sembrar, start=2):
        run_async(sembrar_evento_de_sesion(context["sesion_id"], tipo, secuencia))
    context["estudiante_id"], context["headers"] = run_async(crear_estudiante(comision_id))


@given("una sesión en vivo en estado EnEspera")
def sesion_en_espera(context):
    _preparar(context)


@given("una sesión en vivo en estado EnCurso, en la tercera pregunta")
def sesion_en_curso(context):
    _preparar(context, sembrar=("SesionEnVivoIniciada",))


@given("una sesión en vivo en estado Finalizada")
def sesion_finalizada(context):
    _preparar(context, sembrar=("SesionEnVivoIniciada", "SesionEnVivoFinalizada"))


@given("un Estudiante ya unido a una sesión")
def estudiante_ya_unido(context):
    _preparar(context)
    context["primera"] = run_async(_post_unirse(context["sesion_id"], context["headers"]))
    assert context["primera"].status_code == 200


@given("un sesion_id que no corresponde a ninguna sesión en vivo")
def sesion_inexistente(context):
    _preparar(context)
    context["sesion_id"] = str(uuid.uuid4())


@when("el Estudiante se une")
def estudiante_se_une(context):
    """Une al Estudiante con un Docente conectado al canal, para verificar el broadcast."""
    docente_token = headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)["Authorization"].split()[1]
    sesion_id = context["sesion_id"]
    with TestClient(app) as client:
        with client.websocket_connect(
            f"/sesiones-en-vivo/{sesion_id}/canal?token={docente_token}"
        ) as ws:
            context["response"] = client.post(
                f"/sesiones-en-vivo/{sesion_id}/unirse", headers=context["headers"]
            )
            context["mensaje_docente"] = ws.receive_json()


@when("un Estudiante que no se había unido antes se une ahora")
@when("un Estudiante intenta unirse")
def estudiante_se_une_simple(context):
    context["response"] = run_async(_post_unirse(context["sesion_id"], context["headers"]))


@when("intenta unirse de nuevo")
def estudiante_se_une_de_nuevo(context):
    context["response"] = run_async(_post_unirse(context["sesion_id"], context["headers"]))


@then("se crea su ParticipacionEnVivo y aparece en participantes_por_sesion")
def participacion_creada(context):
    assert context["response"].status_code == 200
    eventos = run_async(_eventos_de_participacion(context["sesion_id"]))
    assert [e["estudiante_id"] for e in eventos] == [context["estudiante_id"]]


@then("el Docente conectado al canal recibe la lista de participantes actualizada")
def docente_recibe_lista(context):
    mensaje = context["mensaje_docente"]
    assert mensaje["tipo"] == "participantes_actualizados"
    assert mensaje["cantidad"] == 1
    assert mensaje["participantes"][0]["estudiante_id"] == context["estudiante_id"]


@then("su ParticipacionEnVivo se crea igualmente, sin respuestas previas registradas")
def participacion_tardia_creada(context):
    assert context["response"].status_code == 200
    eventos = run_async(_eventos_de_participacion(context["sesion_id"]))
    assert len(eventos) == 1
    # Sin respuestas: el único evento del stream es la unión (las respuestas son Iteración 2).
    assert eventos[0]["estudiante_id"] == context["estudiante_id"]


@then(parsers.parse("el sistema responde {codigo:d} sin crear una segunda ParticipacionEnVivo"))
def idempotente(context, codigo):
    assert context["response"].status_code == codigo
    assert context["response"].json() == context["primera"].json()
    assert len(run_async(_eventos_de_participacion(context["sesion_id"]))) == 1


@then(parsers.parse("el sistema rechaza la operación con SesionYaFinalizada ({codigo:d})"))
def rechazo_finalizada(context, codigo):
    assert context["response"].status_code == codigo
    assert "finalizada" in context["response"].json()["detail"]
    assert run_async(_eventos_de_participacion(context["sesion_id"])) == []


@then(parsers.parse("el sistema rechaza la operación con SesionNoExiste ({codigo:d})"))
def rechazo_inexistente(context, codigo):
    assert context["response"].status_code == codigo
