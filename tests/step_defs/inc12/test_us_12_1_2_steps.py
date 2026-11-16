"""Steps BDD de `US-12.1.2` — unirse, consultar y ver el ranking exige pertenecer a la comisión."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from tests.integration.inc6._helpers import (
    crear_estudiante,
    headers_de,
    headers_docente_de_sesion,
    iniciar_y_finalizar,
    preparar_sesion,
)

scenarios("../../features/inc12/US-12.1.2-sesion-en-vivo-por-comision.feature")


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


def _estudiante_de_otra_comision(context) -> None:
    _, comision_c2 = run_async(preparar_sesion())
    _, headers = run_async(crear_estudiante(comision_c2))
    context["headers"] = headers


@given("una sesión en vivo de la comisión C1 y un estudiante de C1")
def sesion_y_estudiante_de_c1(context):
    context["sesion_id"], comision_id = run_async(preparar_sesion())
    _, context["headers"] = run_async(crear_estudiante(comision_id))


@given("una sesión en vivo de la comisión C1 y un estudiante de la comisión C2")
def sesion_y_estudiante_de_c2(context):
    context["sesion_id"], _ = run_async(preparar_sesion())
    _estudiante_de_otra_comision(context)


@given("una sesión finalizada de la comisión C1 y un estudiante de la comisión C2")
def sesion_finalizada_y_estudiante_de_c2(context):
    context["sesion_id"], _ = run_async(preparar_sesion())
    run_async(iniciar_y_finalizar(context["sesion_id"]))
    _estudiante_de_otra_comision(context)


@given("una sesión en vivo de la comisión C1 y un docente asignado solo a C2")
def sesion_y_docente_de_c2(context):
    context["sesion_id"], _ = run_async(preparar_sesion())
    sesion_c2, _ = run_async(preparar_sesion())
    context["headers"] = run_async(headers_docente_de_sesion(sesion_c2))


@given("una sesión en vivo de la comisión C1 y un docente asignado a C1")
def sesion_y_docente_de_c1(context):
    context["sesion_id"], _ = run_async(preparar_sesion())
    context["headers"] = run_async(headers_docente_de_sesion(context["sesion_id"]))


@given("un sesion_id que no corresponde a ninguna sesión")
def sesion_inexistente(context):
    context["sesion_id"] = str(uuid.uuid4())
    context["headers"] = headers_de(uuid.uuid4(), TipoPerfil.ESTUDIANTE)


def _llamar(context, metodo: str, ruta: str = "") -> int:
    with TestClient(app) as client:
        respuesta = client.request(
            metodo, f"/sesiones-en-vivo/{context['sesion_id']}{ruta}", headers=context["headers"]
        )
    return respuesta.status_code


@when(parsers.re(r"el estudiante (?:se une|intenta unirse) a la sesión"))
def se_une(context):
    context["codigos"] = [_llamar(context, "POST", "/unirse")]


@when("el estudiante consulta el estado de la sesión")
@when("el docente consulta el estado de la sesión")
def consulta_estado(context):
    context["codigos"] = [_llamar(context, "GET")]


@when("el estudiante pide el ranking")
def pide_ranking(context):
    context["codigos"] = [_llamar(context, "GET", "/ranking")]


@when("el docente consulta el estado y el ranking")
def consulta_estado_y_ranking(context):
    context["codigos"] = [_llamar(context, "GET"), _llamar(context, "GET", "/ranking")]


@when("un usuario autenticado intenta unirse, consultar el estado o pedir el ranking")
def operaciones_sobre_sesion_inexistente(context):
    context["codigos"] = [
        _llamar(context, "POST", "/unirse"),
        _llamar(context, "GET"),
        _llamar(context, "GET", "/ranking"),
    ]


@then("la unión se acepta")
def union_aceptada(context):
    assert context["codigos"] == [200]


@then("recibe la respuesta")
def recibe_respuesta(context):
    assert context["codigos"] == [200, 200]


@then("se rechaza con 403")
def rechazada_403(context):
    assert context["codigos"] == [403]


@then("se responde 404")
def responde_404(context):
    assert context["codigos"] == [404] * len(context["codigos"])


@then("el estudiante no figura entre los participantes")
def no_figura_entre_participantes(context):
    docente = run_async(headers_docente_de_sesion(context["sesion_id"]))
    with TestClient(app) as client:
        respuesta = client.get(
            f"/sesiones-en-vivo/{context['sesion_id']}/participantes", headers=docente
        )
    assert respuesta.status_code == 200
    assert respuesta.json() == []
