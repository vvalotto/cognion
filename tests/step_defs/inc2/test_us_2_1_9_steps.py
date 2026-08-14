from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenario, then, when
from sqlalchemy import text

from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc2._auth_headers import docente_headers

# El .feature mezcla escenarios backend y frontend (alcance ampliado de US-2.1.9, ver
# docs/specs/inc2/US-2.1.9.md). Solo el escenario backend se ejecuta con pytest-bdd —
# los 3 escenarios frontend se validan con Vitest (Materias.test.tsx, NuevaMateria.test.tsx),
# mismo criterio documentado en docs/plans/inc2/US-2.1.9-context.md.


@scenario(
    "../../features/inc2/US-2.1.9-listado-alta-materias.feature",
    "GET /materias devuelve la cantidad de preguntas activas por materia",
)
def test_get_materias_devuelve_cantidad_preguntas_activas():
    """Escenario backend de US-2.1.9."""


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas_banco_preguntas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_banco_preguntas():
    run_async(_limpiar_tablas_banco_preguntas())
    yield
    run_async(_limpiar_tablas_banco_preguntas())


@pytest.fixture
def context():
    return {}


async def _post_crear_materia(nombre: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/materias", json={"nombre": nombre}, headers=docente_headers())


async def _post_cargar_pregunta_verdadero_falso(banco_id: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            "/preguntas/verdadero-falso",
            json={
                "banco_id": banco_id,
                "texto": "El sol es una estrella.",
                "respuesta_correcta": True,
                "unidad_tematica": "Unidad 1",
                "tema": "Astronomía",
                "dificultad": "medio",
                "importancia": "alto",
            },
            headers=docente_headers(),
        )


async def _delete_eliminar_pregunta(pregunta_id: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.delete(f"/preguntas/{pregunta_id}", headers=docente_headers())


async def _get_listar_materias():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/materias", headers=docente_headers())


@given("una materia con 3 preguntas activas y 1 pregunta eliminada (baja lógica)")
def materia_con_preguntas_activas_e_inactivas(context):
    respuesta_materia = run_async(_post_crear_materia("Ingeniería de Software"))
    assert respuesta_materia.status_code == 201
    context["nombre"] = respuesta_materia.json()["nombre"]
    banco_id = respuesta_materia.json()["banco_id"]

    for _ in range(3):
        respuesta = run_async(_post_cargar_pregunta_verdadero_falso(banco_id))
        assert respuesta.status_code == 201

    a_eliminar = run_async(_post_cargar_pregunta_verdadero_falso(banco_id))
    assert a_eliminar.status_code == 201
    eliminacion = run_async(_delete_eliminar_pregunta(a_eliminar.json()["id"]))
    assert eliminacion.status_code == 204


@when("se hace GET /materias")
def ejecuta_get_materias(context):
    context["response"] = run_async(_get_listar_materias())


@then("la materia aparece en la respuesta con cantidad_preguntas_activas = 3")
def valida_cantidad_preguntas_activas(context):
    assert context["response"].status_code == 200
    materias = {m["nombre"]: m for m in context["response"].json()}
    assert materias[context["nombre"]]["cantidad_preguntas_activas"] == 3
