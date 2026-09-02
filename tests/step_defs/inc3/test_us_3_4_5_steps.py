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
from tests.step_defs.inc3._auth_headers import crear_estudiante_de_materia, docente_headers

scenarios("../../features/inc3/US-3.4.5-mis-materias-actividades.feature")


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
def limpiar_tablas_actividad_evaluativa_y_estudiantes():
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


async def _crear_actividad(
    materia_id: str, apertura: datetime, cierre: datetime, cantidad_preguntas: int = 1
) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/actividades",
            json={
                "materia_id": materia_id,
                "fecha_apertura": apertura.isoformat(),
                "fecha_cierre": cierre.isoformat(),
                "cantidad_preguntas": cantidad_preguntas,
                "cantidad_intentos_permitidos": 1,
                "titulo": "Parcial 1",
            },
            headers=docente_headers(),
        )


async def _get_mis_materias(estudiante_headers: dict) -> object:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/identidad/estudiante/materias", headers=estudiante_headers)


async def _get_mis_actividades(materia_id: str, estudiante_headers: dict) -> object:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(
            "/actividades/mis-actividades",
            params={"materia_id": materia_id},
            headers=estudiante_headers,
        )


async def _finalizar_evaluacion(actividad_id: str, estudiante_headers: dict) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        iniciada = await client.post(
            "/evaluaciones", json={"actividad_id": actividad_id}, headers=estudiante_headers
        )
        await client.post(
            f"/evaluaciones/{iniciada.json()['id']}/finalizar", headers=estudiante_headers
        )


@given("un Estudiante autenticado con comisión asignada")
def estudiante_con_comision(context):
    materia_id = run_async(_crear_materia(f"Ingeniería de Software {uuid.uuid4()}"))
    _estudiante_id, headers = run_async(crear_estudiante_de_materia(materia_id))
    context["materia_id"] = materia_id
    context["estudiante_headers"] = headers


@given("una actividad dentro de su período vigente, sin Evaluacion Finalizada del Estudiante")
def actividad_vigente_sin_evaluacion(context):
    materia_id = run_async(
        _crear_materia_con_preguntas(f"Ingeniería de Software {uuid.uuid4()}", 5)
    )
    _estudiante_id, headers = run_async(crear_estudiante_de_materia(materia_id))
    apertura = datetime.now(UTC) - timedelta(days=1)
    cierre = apertura + timedelta(days=7)
    run_async(_crear_actividad(materia_id, apertura, cierre))
    context["materia_id"] = materia_id
    context["estudiante_headers"] = headers


@given("una actividad con fecha_apertura futura")
def actividad_con_apertura_futura(context):
    materia_id = run_async(
        _crear_materia_con_preguntas(f"Ingeniería de Software {uuid.uuid4()}", 5)
    )
    _estudiante_id, headers = run_async(crear_estudiante_de_materia(materia_id))
    apertura = datetime.now(UTC) + timedelta(days=1)
    cierre = apertura + timedelta(days=7)
    run_async(_crear_actividad(materia_id, apertura, cierre))
    context["materia_id"] = materia_id
    context["estudiante_headers"] = headers


@given("una actividad donde el Estudiante ya tiene una Evaluacion Finalizada")
def actividad_con_evaluacion_finalizada(context):
    materia_id = run_async(
        _crear_materia_con_preguntas(f"Ingeniería de Software {uuid.uuid4()}", 5)
    )
    _estudiante_id, headers = run_async(crear_estudiante_de_materia(materia_id))
    apertura = datetime.now(UTC) - timedelta(days=1)
    cierre = apertura + timedelta(days=7)
    run_async(_crear_actividad(materia_id, apertura, cierre))
    actividad = run_async(_get_mis_actividades(materia_id, headers))
    actividad_id = actividad.json()[0]["id"]
    run_async(_finalizar_evaluacion(actividad_id, headers))
    context["materia_id"] = materia_id
    context["estudiante_headers"] = headers


@given("una materia de su comisión sin actividades creadas")
def materia_sin_actividades(context):
    materia_id = run_async(_crear_materia(f"Gestión de Proyectos {uuid.uuid4()}"))
    _estudiante_id, headers = run_async(crear_estudiante_de_materia(materia_id))
    context["materia_id"] = materia_id
    context["estudiante_headers"] = headers


@when("entra a /mis-actividades/materias")
def entra_a_mis_materias(context):
    context["response"] = run_async(_get_mis_materias(context["estudiante_headers"]))


@when("entra al listado de actividades de esa materia")
def entra_al_listado_de_actividades(context):
    context["response"] = run_async(
        _get_mis_actividades(context["materia_id"], context["estudiante_headers"])
    )


@when("el Estudiante entra al listado")
def estudiante_entra_al_listado(context):
    context["response"] = run_async(
        _get_mis_actividades(context["materia_id"], context["estudiante_headers"])
    )


@when("entra al listado")
def entra_al_listado(context):
    context["response"] = run_async(
        _get_mis_actividades(context["materia_id"], context["estudiante_headers"])
    )


@when("el Estudiante entra a su listado")
def estudiante_entra_a_su_listado(context):
    context["response"] = run_async(
        _get_mis_actividades(context["materia_id"], context["estudiante_headers"])
    )


@then("ve una tarjeta por materia de su comisión")
def ve_tarjeta_por_materia(context):
    assert context["response"].status_code == 200
    data = context["response"].json()
    assert len(data) == 1
    assert data[0]["id"] == context["materia_id"]


@then('la ve con Badge "Pendiente de responder"')
def ve_badge_pendiente(context):
    assert context["response"].status_code == 200
    data = context["response"].json()
    assert len(data) == 1
    assert data[0]["estado"] == "pendiente"


@then('la ve con Badge "Todavía no abrió"')
def ve_badge_todavia_no_abrio(context):
    assert context["response"].status_code == 200
    data = context["response"].json()
    assert len(data) == 1
    assert data[0]["estado"] == "todavia_no_abrio"


@then('la ve con Badge "Finalizada — ver revisión"')
def ve_badge_finalizada(context):
    assert context["response"].status_code == 200
    data = context["response"].json()
    assert len(data) == 1
    assert data[0]["estado"] == "finalizada"
    assert data[0]["evaluacion_id"] is not None


@then("ve la grilla vacía sin actividades pendientes")
def ve_grilla_vacia(context):
    assert context["response"].status_code == 200
    assert context["response"].json() == []
