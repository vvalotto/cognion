"""Steps BDD de `US-12.1.1` — el canal en vivo solo lo abren quienes pertenecen a la comisión."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text
from starlette.websockets import WebSocketDisconnect

from src.app import app
from src.settings import settings
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from tests.integration.inc6._helpers import (
    crear_estudiante,
    headers_de,
    headers_docente_de_sesion,
    preparar_sesion,
)

scenarios("../../features/inc12/US-12.1.1-canal-en-vivo-autorizado.feature")


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
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM usuario"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {}


def _token(headers: dict[str, str]) -> str:
    return headers["Authorization"].split()[1]


def _abrir_canal(sesion_id: str, token: str | None) -> str:
    """Intenta abrir el canal; devuelve `"aceptada"` o `"cerrada:<codigo>"`."""
    url = f"/sesiones-en-vivo/{sesion_id}/canal"
    if token is not None:
        url = f"{url}?token={token}"
    with TestClient(app) as client:
        try:
            with client.websocket_connect(url):
                return "aceptada"
        except WebSocketDisconnect as exc:
            return f"cerrada:{exc.code}"


@given("una sesión en vivo de la comisión C1 y un docente asignado a C1")
def sesion_y_docente_de_c1(context):
    context["sesion_id"], _ = run_async(preparar_sesion())
    context["token"] = _token(run_async(headers_docente_de_sesion(context["sesion_id"])))


@given("una sesión en vivo de la comisión C1 y un estudiante de C1 que todavía no se unió")
def sesion_y_estudiante_de_c1(context):
    context["sesion_id"], comision_id = run_async(preparar_sesion())
    _, headers = run_async(crear_estudiante(comision_id))
    context["token"] = _token(headers)


@given("una sesión en vivo de la comisión C1 y un administrador")
def sesion_y_administrador(context):
    context["sesion_id"], _ = run_async(preparar_sesion())
    context["token"] = _token(headers_de(uuid.uuid4(), TipoPerfil.ADMINISTRADOR))


@given("una sesión en vivo de la comisión C1 y un estudiante de la comisión C2")
def sesion_y_estudiante_de_c2(context):
    context["sesion_id"], _ = run_async(preparar_sesion())
    _, comision_c2 = run_async(preparar_sesion())
    _, headers = run_async(crear_estudiante(comision_c2))
    context["token"] = _token(headers)


@given("una sesión en vivo de la comisión C1 y un docente asignado solo a C2")
def sesion_y_docente_de_c2(context):
    context["sesion_id"], _ = run_async(preparar_sesion())
    sesion_c2, _ = run_async(preparar_sesion())
    context["token"] = _token(run_async(headers_docente_de_sesion(sesion_c2)))


@given("un sesion_id que no corresponde a ninguna sesión")
def sesion_inexistente(context):
    context["sesion_id"] = str(uuid.uuid4())
    context["token"] = _token(headers_de(uuid.uuid4(), TipoPerfil.ESTUDIANTE))


@when(parsers.re(r"el (docente|estudiante|administrador) abre el canal de la sesión"))
def abre_el_canal(context):
    context["resultado"] = _abrir_canal(context["sesion_id"], context["token"])


@when("un usuario autenticado abre el canal")
def usuario_abre_el_canal(context):
    context["resultado"] = _abrir_canal(context["sesion_id"], context["token"])


@when("se abre el canal sin token, o con un token inválido o vencido")
def abre_sin_token_valido(context):
    sesion_id = str(uuid.uuid4())
    vencido = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "rol": TipoPerfil.DOCENTE.value,
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    context["resultados"] = [
        _abrir_canal(sesion_id, None),
        _abrir_canal(sesion_id, "token-invalido"),
        _abrir_canal(sesion_id, vencido),
    ]


@then("la conexión se acepta")
def conexion_aceptada(context):
    assert context["resultado"] == "aceptada"


@then("la conexión se cierra con el código 1008")
def conexion_cerrada(context):
    resultados = context.get("resultados", [context.get("resultado")])
    assert resultados == ["cerrada:1008"] * len(resultados)
