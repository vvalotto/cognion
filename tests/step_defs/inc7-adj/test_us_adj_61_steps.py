"""Steps BDD de US-ADJ-61 — La actividad cerrada se ve como cerrada para el Estudiante."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc3._auth_headers import (
    admin_headers,
    crear_estudiante_de_materia,
    docente_asignado_a_materia,
)

scenarios("../../features/inc7-adj/US-ADJ-61-actividad-cerrada-visible-estudiante.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.execute(text("DELETE FROM invitacion"))
        await session.execute(text("DELETE FROM comision_docentes"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM administrador"))
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


async def _client_call(metodo: str, path: str, **kwargs):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await getattr(client, metodo)(path, **kwargs)


async def _preparar_materia_con_estudiante(context: dict) -> None:
    creada = await _client_call(
        "post",
        "/materias",
        json={"nombre": f"Ingeniería de Software {uuid.uuid4()}"},
        headers=admin_headers(),
    )
    materia_id = creada.json()["id"]
    banco_id = creada.json()["banco_id"]
    _docente_id, docente_headers_ = await docente_asignado_a_materia(materia_id)
    for i in range(5):
        await _client_call(
            "post",
            "/preguntas/verdadero-falso",
            json={
                "banco_id": banco_id,
                "texto": f"Pregunta {i}",
                "respuesta_correcta": True,
                "unidad_tematica": "Unidad 1",
                "tema": "Tema",
                "dificultad": "medio",
                "importancia": "alto",
            },
            headers=docente_headers_,
        )
    _estudiante_id, estudiante_headers = await crear_estudiante_de_materia(materia_id)
    context.update(
        materia_id=materia_id,
        docente_headers=docente_headers_,
        estudiante_headers=estudiante_headers,
    )


async def _crear_actividad(context: dict, apertura: datetime, cierre: datetime) -> str:
    response = await _client_call(
        "post",
        "/actividades",
        json={
            "materia_id": context["materia_id"],
            "fecha_apertura": apertura.isoformat(),
            "fecha_cierre": cierre.isoformat(),
            "cantidad_preguntas": 1,
            "cantidad_intentos_permitidos": 1,
            "titulo": "Parcial 1",
        },
        headers=context["docente_headers"],
    )
    assert response.status_code == 201, response.text
    context["actividad_id"] = response.json()["id"]
    return context["actividad_id"]


def _vigente(context: dict) -> str:
    run_async(_preparar_materia_con_estudiante(context))
    apertura = datetime.now(UTC) - timedelta(days=1)
    return run_async(_crear_actividad(context, apertura, apertura + timedelta(days=7)))


@given("una actividad con cerrada_manualmente = true")
def dado_actividad_cerrada_manualmente(context):
    actividad_id = _vigente(context)
    cerrada = run_async(
        _client_call(
            "post", f"/actividades/{actividad_id}/cerrar", headers=context["docente_headers"]
        )
    )
    assert cerrada.status_code == 200, cerrada.text


@given("una actividad con fecha_cierre en el pasado y cerrada_manualmente = false")
def dado_actividad_vencida(context):
    run_async(_preparar_materia_con_estudiante(context))
    ahora = datetime.now(UTC)
    run_async(_crear_actividad(context, ahora - timedelta(days=8), ahora - timedelta(days=1)))


@given("una actividad con fecha_apertura en el pasado y fecha_cierre en el futuro")
def dado_actividad_vigente(context):
    _vigente(context)


@given("una actividad con fecha_apertura en el futuro")
def dado_actividad_futura(context):
    run_async(_preparar_materia_con_estudiante(context))
    apertura = datetime.now(UTC) + timedelta(days=1)
    run_async(_crear_actividad(context, apertura, apertura + timedelta(days=7)))


@given("una actividad cerrada y un Estudiante con una Evaluacion finalizada de ella")
def dado_actividad_cerrada_con_evaluacion_finalizada(context):
    actividad_id = _vigente(context)
    iniciada = run_async(
        _client_call(
            "post",
            "/evaluaciones",
            json={"actividad_id": actividad_id},
            headers=context["estudiante_headers"],
        )
    )
    assert iniciada.status_code == 200, iniciada.text
    context["evaluacion_id"] = iniciada.json()["id"]
    run_async(
        _client_call(
            "post",
            f"/evaluaciones/{context['evaluacion_id']}/finalizar",
            headers=context["estudiante_headers"],
        )
    )
    cerrada = run_async(
        _client_call(
            "post", f"/actividades/{actividad_id}/cerrar", headers=context["docente_headers"]
        )
    )
    assert cerrada.status_code == 200, cerrada.text


@given("un Estudiante de su comisión sin Evaluacion finalizada")
def dado_estudiante_sin_evaluacion(context):
    # El Estudiante de la comisión ya se creó junto con la materia; no inició ninguna evaluación.
    assert "estudiante_headers" in context


@when("el Estudiante lista las actividades de la materia")
def cuando_lista_actividades(context):
    context["response"] = run_async(
        _client_call(
            "get",
            "/actividades/mis-actividades",
            params={"materia_id": context["materia_id"]},
            headers=context["estudiante_headers"],
        )
    )


@then(parsers.parse('la actividad tiene estado "{estado}"'))
def entonces_estado(context, estado):
    assert context["response"].status_code == 200
    data = context["response"].json()
    assert len(data) == 1
    assert data[0]["estado"] == estado


@then('la actividad tiene estado "finalizada" y trae su evaluacion_id')
def entonces_finalizada_con_evaluacion_id(context):
    data = context["response"].json()
    assert data[0]["estado"] == "finalizada"
    assert data[0]["evaluacion_id"] == context["evaluacion_id"]
