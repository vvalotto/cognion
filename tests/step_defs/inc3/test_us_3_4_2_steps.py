from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc3._auth_headers import docente_headers

scenarios("../../features/inc3/US-3.4.2-listado-materias-actividades-docente.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_actividad_evaluativa():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {}


async def _crear_materia(nombre: str) -> str:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        creada = await client.post("/materias", json={"nombre": nombre}, headers=docente_headers())
        return creada.json()["id"]


async def _crear_materia_con_preguntas(nombre: str, cantidad: int) -> str:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        creada = await client.post("/materias", json={"nombre": nombre}, headers=docente_headers())
        banco_id = creada.json()["banco_id"]
        for i in range(cantidad):
            await client.post(
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
                headers=docente_headers(),
            )
        return creada.json()["id"]


async def _crear_actividad(materia_id: str) -> None:
    apertura = datetime.now(UTC)
    cierre = apertura + timedelta(days=7)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/actividades",
            json={
                "materia_id": materia_id,
                "fecha_apertura": apertura.isoformat(),
                "fecha_cierre": cierre.isoformat(),
                "cantidad_preguntas": 10,
                "cantidad_intentos_permitidos": 1,
                "titulo": "Parcial 1",
            },
            headers=docente_headers(),
        )


async def _get_materias():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/materias", headers=docente_headers())


async def _get_actividades(materia_id: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(
            "/actividades", params={"materia_id": materia_id}, headers=docente_headers()
        )


@given("un Docente autenticado con materias asignadas")
def docente_con_materias(context):
    run_async(_crear_materia(f"Ingeniería de Software {uuid.uuid4()}"))


@given("un Docente en /actividad-evaluativa/materias")
def docente_en_materias(context):
    context["materia_id"] = run_async(
        _crear_materia_con_preguntas(f"Ingeniería de Software {uuid.uuid4()}", 20)
    )
    run_async(_crear_actividad(context["materia_id"]))


@given("una materia sin actividades creadas")
def materia_sin_actividades(context):
    context["materia_id"] = run_async(_crear_materia(f"Gestión de Proyectos {uuid.uuid4()}"))


@when("entra a /actividad-evaluativa/materias")
def entra_a_materias(context):
    context["response"] = run_async(_get_materias())


@when("elige una materia")
def elige_una_materia(context):
    context["response"] = run_async(_get_actividades(context["materia_id"]))


@when("el Docente entra a su listado")
def docente_entra_a_su_listado(context):
    context["response"] = run_async(_get_actividades(context["materia_id"]))


@then("ve una tarjeta por materia")
def ve_una_tarjeta_por_materia(context):
    assert context["response"].status_code == 200
    assert len(context["response"].json()) >= 1


@then("ve el listado de sus actividades con estado (En curso / Programada / Cerrada)")
def ve_listado_con_estado(context):
    data = context["response"].json()
    assert context["response"].status_code == 200
    assert len(data) == 1
    assert data[0]["estado"] in {"en_curso", "programada", "cerrada"}


@then('ve la grilla vacía con la acción "+ Nueva actividad" disponible')
def ve_grilla_vacia(context):
    """El botón "+ Nueva actividad" siempre está visible — verificado en Vitest (frontend),
    no es un dato que devuelva la API. Acá se verifica la única condición observable por HTTP:
    la grilla vacía.
    """
    assert context["response"].status_code == 200
    assert context["response"].json() == []
