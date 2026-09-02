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
from tests.step_defs.inc3._auth_headers import crear_estudiante, docente_headers

scenarios("../../features/inc3/US-3.4.4-detalle-actividad.feature")


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


def _periodo() -> tuple[str, str]:
    apertura = datetime.now(UTC)
    cierre = apertura + timedelta(days=7)
    return apertura.isoformat(), cierre.isoformat()


async def _crear_actividad(materia_id: str) -> str:
    apertura, cierre = _periodo()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        creada = await client.post(
            "/actividades",
            json={
                "materia_id": materia_id,
                "fecha_apertura": apertura,
                "fecha_cierre": cierre,
                "cantidad_preguntas": 10,
                "cantidad_intentos_permitidos": 1,
                "titulo": "Parcial 1",
            },
            headers=docente_headers(),
        )
        return creada.json()["id"]


async def _iniciar_evaluacion(actividad_id: str) -> None:
    _, headers = await crear_estudiante()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/evaluaciones", json={"actividad_id": actividad_id}, headers=headers)


async def _get_actividad(actividad_id: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(f"/actividades/{actividad_id}", headers=docente_headers())


async def _modificar_periodo(actividad_id: str, nueva_fecha_cierre: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.patch(
            f"/actividades/{actividad_id}/periodo",
            json={"nueva_fecha_cierre": nueva_fecha_cierre},
            headers=docente_headers(),
        )


async def _cerrar_actividad(actividad_id: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(f"/actividades/{actividad_id}/cerrar", headers=docente_headers())


@given("un Docente en el listado de actividades", target_fixture="context")
def docente_en_listado(context):
    materia_id = run_async(
        _crear_materia_con_preguntas(f"Ingeniería de Software {uuid.uuid4()}", 20)
    )
    context["actividad_id"] = run_async(_crear_actividad(materia_id))
    return context


@when("elige una actividad")
def elige_una_actividad(context):
    context["response"] = run_async(_get_actividad(context["actividad_id"]))


@then("ve apertura, cierre, cantidad de preguntas, intentos, evaluaciones activas y finalizadas")
def ve_detalle_completo(context):
    assert context["response"].status_code == 200
    data = context["response"].json()
    assert {
        "fecha_apertura",
        "fecha_cierre",
        "cantidad_preguntas",
        "cantidad_intentos_permitidos",
        "cantidad_evaluaciones_activas",
        "cantidad_evaluaciones_finalizadas",
    } <= data.keys()


@given("un Docente en el detalle de una actividad no cerrada", target_fixture="context")
def docente_en_detalle_no_cerrada(context):
    materia_id = run_async(
        _crear_materia_con_preguntas(f"Ingeniería de Software {uuid.uuid4()}", 20)
    )
    context["actividad_id"] = run_async(_crear_actividad(materia_id))
    return context


@when('va a "Extender plazo" y guarda una fecha de cierre posterior')
def extiende_el_plazo(context):
    _, cierre_actual = _periodo()
    nueva_fecha = (datetime.now(UTC) + timedelta(days=14)).isoformat()
    context["response"] = run_async(_modificar_periodo(context["actividad_id"], nueva_fecha))
    context["nueva_fecha"] = nueva_fecha


@then("el sistema actualiza el cierre")
def sistema_actualiza_el_cierre(context):
    assert context["response"].status_code == 200


@then("vuelve al detalle mostrando el nuevo valor")
def vuelve_al_detalle_con_nuevo_valor(context):
    """La navegación de vuelta al detalle es un comportamiento de UI — verificado en
    `ExtenderPlazo.test.tsx` (Vitest). Acá se verifica la única condición observable por HTTP:
    el detalle refleja el nuevo cierre.
    """
    detalle = run_async(_get_actividad(context["actividad_id"]))
    fecha_cierre = datetime.fromisoformat(detalle.json()["fecha_cierre"])
    esperada = datetime.fromisoformat(context["nueva_fecha"])
    assert fecha_cierre == esperada


@given("una actividad con evaluaciones activas", target_fixture="context")
def actividad_con_evaluaciones_activas(context):
    materia_id = run_async(
        _crear_materia_con_preguntas(f"Ingeniería de Software {uuid.uuid4()}", 20)
    )
    context["actividad_id"] = run_async(_crear_actividad(materia_id))
    run_async(_iniciar_evaluacion(context["actividad_id"]))
    return context


@when("el Docente intenta guardar un cierre anterior al actual")
def intenta_acortar_el_plazo(context):
    cierre_anterior = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    context["response"] = run_async(_modificar_periodo(context["actividad_id"], cierre_anterior))


@then("el backend responde 422 NoSePuedeAcortarConEvaluacionesActivas")
def backend_responde_422(context):
    assert context["response"].status_code == 422
    assert "acortar" in context["response"].json()["detail"]


@then("el formulario muestra el error inline sin navegar")
def formulario_muestra_error_inline(context):
    """Comportamiento de UI — verificado en `ExtenderPlazo.test.tsx` (Vitest). Acá se verifica
    la única condición observable por HTTP: el 422 ya afirmado no cambió el estado del recurso.
    """
    detalle = run_async(_get_actividad(context["actividad_id"]))
    assert detalle.json()["cerrada_manualmente"] is False


@when('confirma "Sí, cerrar actividad ahora"')
def confirma_cierre(context):
    run_async(_iniciar_evaluacion(context["actividad_id"]))
    context["response"] = run_async(_cerrar_actividad(context["actividad_id"]))


@then("el sistema cierra la actividad y finaliza en cascada sus evaluaciones activas")
def sistema_cierra_y_finaliza_en_cascada(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["cerrada_manualmente"] is True


@then("vuelve al detalle mostrando el estado Cerrada")
def vuelve_al_detalle_con_estado_cerrada(context):
    """La navegación de vuelta al detalle es un comportamiento de UI — verificado en
    `CerrarActividad.test.tsx` (Vitest). Acá se verifica la condición observable por HTTP.
    """
    detalle = run_async(_get_actividad(context["actividad_id"]))
    assert detalle.json()["estado"] == "cerrada"
