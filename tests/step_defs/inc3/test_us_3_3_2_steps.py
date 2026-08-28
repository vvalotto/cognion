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
from tests.step_defs.inc3._auth_headers import crear_estudiante, docente_headers

scenarios("../../features/inc3/US-3.3.2-cerrar-actividad.feature")


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


def _periodo_vigente() -> tuple[datetime, datetime]:
    apertura = datetime.now(UTC) - timedelta(days=1)
    return apertura, apertura + timedelta(days=7)


async def _crear_materia_con_verdadero_falso() -> str:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        creada = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=docente_headers()
        )
        banco_id = creada.json()["banco_id"]
        await client.post(
            "/preguntas/verdadero-falso",
            json={
                "banco_id": banco_id,
                "texto": f"Pregunta {uuid.uuid4()}",
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
    materia_id: str, fecha_apertura: datetime, fecha_cierre: datetime
) -> dict:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/actividades",
            json={
                "materia_id": materia_id,
                "fecha_apertura": fecha_apertura.isoformat(),
                "fecha_cierre": fecha_cierre.isoformat(),
                "cantidad_preguntas": 1,
                "cantidad_intentos_permitidos": 1,
            },
            headers=docente_headers(),
        )
        return response.json()


async def _iniciar_evaluacion(actividad_id: str, estudiante_headers: dict) -> dict:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/evaluaciones", json={"actividad_id": actividad_id}, headers=estudiante_headers
        )
        return response.json()


async def _suspender(evaluacion_id: str, estudiante_headers: dict) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(f"/evaluaciones/{evaluacion_id}/suspender", headers=estudiante_headers)


async def _cerrar_actividad(actividad_id: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(f"/actividades/{actividad_id}/cerrar", headers=docente_headers())


async def _modificar_periodo(actividad_id: str, nueva_fecha_cierre: datetime):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.patch(
            f"/actividades/{actividad_id}/periodo",
            json={"nueva_fecha_cierre": nueva_fecha_cierre.isoformat()},
            headers=docente_headers(),
        )


async def _contar_eventos(aggregate_type: str, aggregate_id: str, event_type: str) -> int:
    async with SessionLocal() as session:
        resultado = await session.execute(
            text(
                "SELECT count(*) FROM events WHERE aggregate_type = :aggregate_type "
                "AND aggregate_id = :id AND event_type = :event_type"
            ),
            {"aggregate_type": aggregate_type, "id": aggregate_id, "event_type": event_type},
        )
        return resultado.scalar_one()


async def _ultimo_actor(evaluacion_id: str, event_type: str) -> str:
    async with SessionLocal() as session:
        resultado = await session.execute(
            text(
                "SELECT payload->>'actor' FROM events WHERE aggregate_type = 'Evaluacion' "
                "AND aggregate_id = :id AND event_type = :event_type "
                "ORDER BY sequence_number DESC LIMIT 1"
            ),
            {"id": evaluacion_id, "event_type": event_type},
        )
        return resultado.scalar_one()


async def _armar_actividad() -> dict:
    materia_id = await _crear_materia_con_verdadero_falso()
    apertura, cierre = _periodo_vigente()
    actividad = await _crear_actividad(materia_id, apertura, cierre)
    return {"actividad": actividad, "cierre": cierre, "apertura": apertura}


@given("una ActividadEvaluativaPeriodoAbierto vigente sin ninguna Evaluacion EnCurso o Suspendida")
def actividad_vigente_sin_evaluaciones(context):
    context.update(run_async(_armar_actividad()))


@given("una ActividadEvaluativaPeriodoAbierto vigente")
def actividad_vigente(context):
    context.update(run_async(_armar_actividad()))


@given("existen dos Evaluacion EnCurso de esa actividad")
def dos_evaluaciones_en_curso(context):
    evaluaciones = []
    for _ in range(2):
        _estudiante_id, headers = run_async(crear_estudiante())
        evaluacion = run_async(_iniciar_evaluacion(context["actividad"]["id"], headers))
        evaluaciones.append(evaluacion)
    context["evaluaciones"] = evaluaciones


@given("existe una Evaluacion Suspendida de esa actividad")
def evaluacion_suspendida_de_esa_actividad(context):
    _estudiante_id, headers = run_async(crear_estudiante())
    evaluacion = run_async(_iniciar_evaluacion(context["actividad"]["id"], headers))
    run_async(_suspender(evaluacion["id"], headers))
    context["evaluacion"] = evaluacion


@given(parsers.parse("una ActividadEvaluativaPeriodoAbierto con cerrada_manualmente = {valor}"))
def actividad_con_cerrada_manualmente(context, valor):
    datos = run_async(_armar_actividad())
    context.update(datos)
    if valor == "true":
        run_async(_cerrar_actividad(context["actividad"]["id"]))


@when("el Docente ejecuta CerrarActividad")
@when("el Docente ejecuta CerrarActividad de nuevo")
def ejecuta_cerrar_actividad(context):
    context["response"] = run_async(_cerrar_actividad(context["actividad"]["id"]))


@when("el Docente ejecuta CerrarActividad sobre un actividad_id que no existe")
def ejecuta_cerrar_actividad_inexistente(context):
    context["response"] = run_async(_cerrar_actividad(str(uuid.uuid4())))


@when("el Docente ejecuta ModificarPeriodoDisponibilidad")
def ejecuta_modificar_periodo(context):
    nueva_fecha_cierre = context["cierre"] + timedelta(days=1)
    context["response"] = run_async(
        _modificar_periodo(context["actividad"]["id"], nueva_fecha_cierre)
    )


@then("se emite ActividadEvaluativaCerrada")
def valida_emite_actividad_cerrada(context):
    assert (
        run_async(
            _contar_eventos(
                "ActividadEvaluativaPeriodoAbierto",
                context["actividad"]["id"],
                "ActividadEvaluativaCerrada",
            )
        )
        == 1
    )


@then("cerrada_manualmente pasa a true")
def valida_cerrada_manualmente(context):
    assert context["response"].json()["cerrada_manualmente"] is True


@then("ambas Evaluacion pasan a Finalizada")
def valida_ambas_finalizadas(context):
    for evaluacion in context["evaluaciones"]:
        assert (
            run_async(_contar_eventos("Evaluacion", evaluacion["id"], "EvaluacionFinalizada")) == 1
        )


@then('cada una emite EvaluacionFinalizada con actor "sistema"')
def valida_actor_sistema_en_ambas(context):
    for evaluacion in context["evaluaciones"]:
        assert run_async(_ultimo_actor(evaluacion["id"], "EvaluacionFinalizada")) == "sistema"


@then("la Evaluacion pasa a Finalizada")
def valida_evaluacion_finalizada(context):
    assert (
        run_async(
            _contar_eventos("Evaluacion", context["evaluacion"]["id"], "EvaluacionFinalizada")
        )
        == 1
    )


@then("se rechaza con ActividadYaCerrada")
def valida_rechaza_actividad_ya_cerrada(context):
    assert context["response"].status_code == 422


@then("no se emite un segundo ActividadEvaluativaCerrada")
def valida_sin_segundo_evento(context):
    assert (
        run_async(
            _contar_eventos(
                "ActividadEvaluativaPeriodoAbierto",
                context["actividad"]["id"],
                "ActividadEvaluativaCerrada",
            )
        )
        == 1
    )


@then("se rechaza con ActividadNoExiste")
def valida_rechaza_actividad_no_existe(context):
    assert context["response"].status_code == 404
