from __future__ import annotations

import asyncio
import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc3._auth_headers import crear_estudiante, docente_headers

scenarios("../../features/inc3/US-3.2.2-suspender-reanudar-evaluacion.feature")


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


async def _contar_eventos(evaluacion_id: str, event_type: str | None = None) -> int:
    async with SessionLocal() as session:
        query = (
            "SELECT count(*) FROM events WHERE aggregate_type = 'Evaluacion' AND aggregate_id = :id"
        )
        params: dict[str, object] = {"id": evaluacion_id}
        if event_type is not None:
            query += " AND event_type = :event_type"
            params["event_type"] = event_type
        resultado = await session.execute(text(query), params)
        return resultado.scalar_one()


async def _crear_materia_con_verdadero_falso() -> tuple[str, str]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        creada = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=docente_headers()
        )
        banco_id = creada.json()["banco_id"]
        respuesta = await client.post(
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
        return creada.json()["id"], respuesta.json()["id"]


async def _crear_actividad(
    materia_id: str, fecha_apertura: datetime, fecha_cierre: datetime
) -> str:
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
        return response.json()["id"]


async def _iniciar_evaluacion(actividad_id: str, estudiante_headers: dict) -> dict:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/evaluaciones", json={"actividad_id": actividad_id}, headers=estudiante_headers
        )
        return response.json()


async def _suspender(evaluacion_id: str, estudiante_headers: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            f"/evaluaciones/{evaluacion_id}/suspender", headers=estudiante_headers
        )


async def _reanudar(evaluacion_id: str, estudiante_headers: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            f"/evaluaciones/{evaluacion_id}/reanudar", headers=estudiante_headers
        )


async def _registrar_respuesta(evaluacion_id: str, pregunta_id: str, estudiante_headers: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            f"/evaluaciones/{evaluacion_id}/respuestas",
            json={"pregunta_id": pregunta_id, "contenido": {"valor": True}},
            headers=estudiante_headers,
        )


def _periodo_vigente() -> tuple[datetime, datetime]:
    apertura = datetime.now(UTC) - timedelta(days=1)
    return apertura, apertura + timedelta(days=7)


async def _armar_evaluacion_en_curso():
    materia_id, pregunta_id = await _crear_materia_con_verdadero_falso()
    apertura, cierre = _periodo_vigente()
    actividad_id = await _crear_actividad(materia_id, apertura, cierre)
    _estudiante_id, headers = await crear_estudiante()
    evaluacion = await _iniciar_evaluacion(actividad_id, headers)
    return evaluacion, pregunta_id, headers


@given("una Evaluacion EnCurso")
def evaluacion_en_curso(context):
    evaluacion, pregunta_id, headers = run_async(_armar_evaluacion_en_curso())
    context["evaluacion"] = evaluacion
    context["pregunta_id"] = pregunta_id
    context["estudiante_headers"] = headers


@given("una Evaluacion Suspendida con respuestas ya registradas")
def evaluacion_suspendida_con_respuestas(context):
    evaluacion, pregunta_id, headers = run_async(_armar_evaluacion_en_curso())
    run_async(_registrar_respuesta(evaluacion["id"], pregunta_id, headers))
    run_async(_suspender(evaluacion["id"], headers))
    context["evaluacion"] = evaluacion
    context["pregunta_id"] = pregunta_id
    context["estudiante_headers"] = headers


@given("una Evaluacion recién reanudada")
def evaluacion_recien_reanudada(context):
    evaluacion, pregunta_id, headers = run_async(_armar_evaluacion_en_curso())
    run_async(_suspender(evaluacion["id"], headers))
    run_async(_reanudar(evaluacion["id"], headers))
    context["evaluacion"] = evaluacion
    context["pregunta_id"] = pregunta_id
    context["estudiante_headers"] = headers


@given("una Evaluacion Suspendida")
def evaluacion_suspendida(context):
    evaluacion, pregunta_id, headers = run_async(_armar_evaluacion_en_curso())
    run_async(_suspender(evaluacion["id"], headers))
    context["evaluacion"] = evaluacion
    context["pregunta_id"] = pregunta_id
    context["estudiante_headers"] = headers


@given("una Evaluacion Finalizada")
def evaluacion_finalizada(context):
    from src.actividad_evaluativa.entities.evaluacion import (
        EstadoEvaluacion,
        Evaluacion,
        PreguntaAsignada,
    )

    pregunta_id = uuid.uuid4()
    evaluacion = Evaluacion.crear(
        uuid.uuid4(), uuid.uuid4(), [PreguntaAsignada(pregunta_id=pregunta_id, orden=0)]
    )
    evaluacion.estado = EstadoEvaluacion.FINALIZADA
    context["evaluacion_dominio"] = evaluacion


@given("una Evaluacion Suspendida cuya actividad ya pasó su fecha_cierre")
def evaluacion_suspendida_actividad_por_cerrar(context):
    materia_id, pregunta_id = run_async(_crear_materia_con_verdadero_falso())
    apertura = datetime.now(UTC) - timedelta(seconds=1)
    cierre = datetime.now(UTC) + timedelta(seconds=3)
    actividad_id = run_async(_crear_actividad(materia_id, apertura, cierre))
    _estudiante_id, headers = run_async(crear_estudiante())
    evaluacion = run_async(_iniciar_evaluacion(actividad_id, headers))
    run_async(_suspender(evaluacion["id"], headers))
    time.sleep(4)  # deja pasar fecha_cierre antes de intentar ReanudarEvaluacion
    context["evaluacion"] = evaluacion
    context["pregunta_id"] = pregunta_id
    context["estudiante_headers"] = headers


@given("una Evaluacion EnCurso cuya actividad ya pasó su fecha_cierre")
def evaluacion_en_curso_actividad_por_cerrar(context):
    materia_id, pregunta_id = run_async(_crear_materia_con_verdadero_falso())
    apertura = datetime.now(UTC) - timedelta(seconds=1)
    cierre = datetime.now(UTC) + timedelta(seconds=3)
    actividad_id = run_async(_crear_actividad(materia_id, apertura, cierre))
    _estudiante_id, headers = run_async(crear_estudiante())
    evaluacion = run_async(_iniciar_evaluacion(actividad_id, headers))
    time.sleep(4)  # deja pasar fecha_cierre antes de intentar SuspenderEvaluacion
    context["evaluacion"] = evaluacion
    context["pregunta_id"] = pregunta_id
    context["estudiante_headers"] = headers


@when("el Estudiante ejecuta SuspenderEvaluacion(evaluacion_id)")
@when("el Estudiante ejecuta SuspenderEvaluacion")
def ejecuta_suspender_evaluacion(context):
    context["response"] = run_async(
        _suspender(context["evaluacion"]["id"], context["estudiante_headers"])
    )


@when("el Estudiante ejecuta ReanudarEvaluacion(evaluacion_id)")
def ejecuta_reanudar_evaluacion(context):
    context["response"] = run_async(
        _reanudar(context["evaluacion"]["id"], context["estudiante_headers"])
    )


@when("el Estudiante confirma una respuesta")
def estudiante_confirma_respuesta(context):
    context["response"] = run_async(
        _registrar_respuesta(
            context["evaluacion"]["id"], context["pregunta_id"], context["estudiante_headers"]
        )
    )


@when("el Estudiante intenta SuspenderEvaluacion de nuevo")
def intenta_suspender_de_nuevo(context):
    context["response"] = run_async(
        _suspender(context["evaluacion"]["id"], context["estudiante_headers"])
    )


@when("el Estudiante intenta SuspenderEvaluacion")
def intenta_suspender(context):
    if "evaluacion_dominio" in context:
        try:
            context["evaluacion_dominio"].validar_para_suspender()
            context["error_dominio"] = None
        except Exception as exc:  # noqa: BLE001 — capturado para inspección en el Then
            context["error_dominio"] = exc
        return

    context["response"] = run_async(
        _suspender(context["evaluacion"]["id"], context["estudiante_headers"])
    )


@when("el Estudiante intenta ReanudarEvaluacion")
def intenta_reanudar(context):
    if "evaluacion_dominio" in context:
        try:
            context["evaluacion_dominio"].validar_para_reanudar()
            context["error_dominio"] = None
        except Exception as exc:  # noqa: BLE001 — capturado para inspección en el Then
            context["error_dominio"] = exc
        return

    context["response"] = run_async(
        _reanudar(context["evaluacion"]["id"], context["estudiante_headers"])
    )


@then("el estado pasa a Suspendida")
def valida_estado_suspendida(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["estado"] == "Suspendida"


@then("se emite el evento EvaluacionSuspendida")
def valida_evento_suspendida(context):
    evaluacion_id = context["evaluacion"]["id"]
    assert run_async(_contar_eventos(evaluacion_id, "EvaluacionSuspendida")) == 1


@then("el estado pasa a EnCurso")
def valida_estado_en_curso(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["estado"] == "EnCurso"


@then("se emite el evento EvaluacionReanudada")
def valida_evento_reanudada(context):
    evaluacion_id = context["evaluacion"]["id"]
    assert run_async(_contar_eventos(evaluacion_id, "EvaluacionReanudada")) == 1


@then("las respuestas y el set de preguntas asignadas no cambian")
def valida_respuestas_y_set_sin_cambios(context):
    respuesta = context["response"].json()
    assert respuesta["preguntas_asignadas"] == context["evaluacion"]["preguntas_asignadas"]


@then("el sistema la registra normalmente sin EvaluacionSuspendida")
def valida_registro_normal(context):
    assert context["response"].status_code == 201


@then("el sistema rechaza la operación con EvaluacionYaSuspendida")
def valida_rechazo_evaluacion_ya_suspendida(context):
    assert context["response"].status_code == 422


@then("el sistema rechaza la operación con EvaluacionYaFinalizada")
def valida_rechazo_evaluacion_ya_finalizada(context):
    from src.actividad_evaluativa.entities.errors import EvaluacionYaFinalizada

    assert isinstance(context["error_dominio"], EvaluacionYaFinalizada)


@then("el sistema rechaza la operación con EvaluacionNoSuspendida")
def valida_rechazo_evaluacion_no_suspendida(context):
    assert context["response"].status_code == 422


@then("el sistema rechaza la operación con FueraDePeriodo")
def valida_rechazo_fuera_de_periodo(context):
    assert context["response"].status_code == 422


@then("el sistema acepta la operación y el estado pasa a Suspendida")
def valida_acepta_y_pasa_a_suspendida(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["estado"] == "Suspendida"
