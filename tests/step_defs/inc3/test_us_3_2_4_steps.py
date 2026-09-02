from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.actividad_evaluativa.frameworks.adapters.evaluacion_activa_query_repository import (
    SQLAlchemyEvaluacionActivaQueryRepository,
)
from src.actividad_evaluativa.frameworks.dependencies import (
    build_verificar_vencimientos_use_case,
)
from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc3._auth_headers import crear_estudiante, docente_headers

scenarios("../../features/inc3/US-3.2.4-verificador-vencimientos.feature")


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


async def _contar_eventos(evaluacion_id: str, event_type: str) -> int:
    async with SessionLocal() as session:
        resultado = await session.execute(
            text(
                "SELECT count(*) FROM events WHERE aggregate_type = 'Evaluacion' "
                "AND aggregate_id = :id AND event_type = :event_type"
            ),
            {"id": evaluacion_id, "event_type": event_type},
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


async def _finalizar(evaluacion_id: str, estudiante_headers: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            f"/evaluaciones/{evaluacion_id}/finalizar", headers=estudiante_headers
        )


async def _backdatear_ultima_actividad(evaluacion_id: str, momento: datetime) -> None:
    async with SessionLocal() as session:
        await session.execute(
            text(
                "UPDATE events SET occurred_at = :momento "
                "WHERE aggregate_type = 'Evaluacion' AND aggregate_id = :id "
                "AND event_type = 'EvaluacionIniciada'"
            ),
            {"momento": momento, "id": evaluacion_id},
        )
        await session.commit()


async def _backdatear_fecha_cierre(actividad_id: str, nueva_fecha_cierre: datetime) -> None:
    async with SessionLocal() as session:
        await session.execute(
            text(
                "UPDATE events SET payload = jsonb_set("
                "payload, '{fecha_cierre}', to_jsonb(CAST(:fecha AS text))) "
                "WHERE aggregate_type = 'ActividadEvaluativaPeriodoAbierto' "
                "AND aggregate_id = :actividad_id"
            ),
            {"fecha": nueva_fecha_cierre.isoformat(), "actividad_id": actividad_id},
        )
        await session.commit()


def _periodo_vigente() -> tuple[datetime, datetime]:
    apertura = datetime.now(UTC) - timedelta(days=1)
    return apertura, apertura + timedelta(days=7)


async def _armar_evaluacion_en_curso(fecha_cierre: datetime | None = None) -> dict:
    materia_id, _pregunta_id = await _crear_materia_con_verdadero_falso()
    apertura, cierre = _periodo_vigente()
    actividad_id = await _crear_actividad(materia_id, apertura, fecha_cierre or cierre)
    _estudiante_id, headers = await crear_estudiante()
    evaluacion = await _iniciar_evaluacion(actividad_id, headers)
    return {"evaluacion": evaluacion, "actividad_id": actividad_id, "estudiante_headers": headers}


async def _ejecutar_verificador() -> object:
    async with SessionLocal() as session:
        use_case = build_verificar_vencimientos_use_case(session)
        return await use_case.execute()


@given("una Evaluacion EnCurso cuya ultima_actividad_en supera el UMBRAL_INACTIVIDAD")
def evaluacion_en_curso_inactiva(context):
    datos = run_async(_armar_evaluacion_en_curso())
    run_async(
        _backdatear_ultima_actividad(
            datos["evaluacion"]["id"], datetime.now(UTC) - timedelta(minutes=30)
        )
    )
    context.update(datos)


@given("una Evaluacion EnCurso cuya ultima_actividad_en es menor al UMBRAL_INACTIVIDAD")
def evaluacion_en_curso_activa(context):
    context.update(run_async(_armar_evaluacion_en_curso()))


@given("una ActividadEvaluativaPeriodoAbierto con fecha_cierre en el pasado")
def actividad_vencida(context):
    context["fecha_cierre_vencida"] = True


@given("una ActividadEvaluativaPeriodoAbierto con fecha_cierre en el futuro")
def actividad_vigente(context):
    context["fecha_cierre_vencida"] = False


@given("una Evaluacion EnCurso de esa actividad")
def evaluacion_en_curso_de_actividad(context):
    datos = run_async(_armar_evaluacion_en_curso())
    if context.get("fecha_cierre_vencida"):
        run_async(
            _backdatear_fecha_cierre(datos["actividad_id"], datetime.now(UTC) - timedelta(days=1))
        )
    context.update(datos)


@given("una Evaluacion Suspendida de esa actividad")
def evaluacion_suspendida_de_actividad(context):
    datos = run_async(_armar_evaluacion_en_curso())
    run_async(_suspender(datos["evaluacion"]["id"], datos["estudiante_headers"]))
    if context.get("fecha_cierre_vencida"):
        run_async(
            _backdatear_fecha_cierre(datos["actividad_id"], datetime.now(UTC) - timedelta(days=1))
        )
    context.update(datos)


@given(
    "una Evaluacion que ya fue Suspendida por una corrida anterior de VerificarVencimientosUseCase"
)
def evaluacion_ya_suspendida_por_corrida_anterior(context):
    datos = run_async(_armar_evaluacion_en_curso())
    run_async(
        _backdatear_ultima_actividad(
            datos["evaluacion"]["id"], datetime.now(UTC) - timedelta(minutes=30)
        )
    )
    context.update(datos)
    context["resultado"] = run_async(_ejecutar_verificador())
    assert context["resultado"].suspendidas == 1


@given("una Evaluacion Finalizada")
def evaluacion_finalizada(context):
    datos = run_async(_armar_evaluacion_en_curso())
    run_async(_finalizar(datos["evaluacion"]["id"], datos["estudiante_headers"]))
    context.update(datos)


@when("se ejecuta VerificarVencimientosUseCase")
@when("se ejecuta VerificarVencimientosUseCase de nuevo")
def ejecuta_verificador(context):
    context["resultado"] = run_async(_ejecutar_verificador())


@then("la Evaluacion pasa a Suspendida")
def valida_pasa_a_suspendida(context):
    assert run_async(_contar_eventos(context["evaluacion"]["id"], "EvaluacionSuspendida")) == 1


@then('se emite EvaluacionSuspendida con actor "sistema"')
def valida_emite_suspendida_actor_sistema(context):
    assert (
        run_async(_ultimo_actor(context["evaluacion"]["id"], "EvaluacionSuspendida")) == "sistema"
    )


@then("la Evaluacion sigue EnCurso")
def valida_sigue_en_curso(context):
    assert run_async(_contar_eventos(context["evaluacion"]["id"], "EvaluacionSuspendida")) == 0
    assert run_async(_contar_eventos(context["evaluacion"]["id"], "EvaluacionFinalizada")) == 0


@then("no se emite ningun evento nuevo")
def valida_sin_eventos_nuevos(context):
    total = run_async(_contar_eventos(context["evaluacion"]["id"], "EvaluacionSuspendida"))
    total += run_async(_contar_eventos(context["evaluacion"]["id"], "EvaluacionFinalizada"))
    assert total == 0


@then("la Evaluacion pasa a Finalizada")
def valida_pasa_a_finalizada(context):
    assert run_async(_contar_eventos(context["evaluacion"]["id"], "EvaluacionFinalizada")) == 1


@then('se emite EvaluacionFinalizada con actor "sistema"')
def valida_emite_finalizada_actor_sistema(context):
    assert (
        run_async(_ultimo_actor(context["evaluacion"]["id"], "EvaluacionFinalizada")) == "sistema"
    )


@then("la Evaluacion sigue Suspendida")
def valida_sigue_suspendida(context):
    assert run_async(_contar_eventos(context["evaluacion"]["id"], "EvaluacionSuspendida")) == 1
    assert run_async(_contar_eventos(context["evaluacion"]["id"], "EvaluacionFinalizada")) == 0


@then("no se levanta ninguna excepcion")
def valida_sin_excepcion(context):
    assert context["resultado"] is not None


@then("no se emite un segundo EvaluacionSuspendida")
def valida_sin_segundo_suspendida(context):
    assert run_async(_contar_eventos(context["evaluacion"]["id"], "EvaluacionSuspendida")) == 1


@then("la Evaluacion no aparece en el resultado de EvaluacionActivaQueryPort.listar_no_finalizadas")
def valida_no_aparece_en_listar_no_finalizadas(context):
    async def _verificar() -> bool:
        async with SessionLocal() as session:
            repo = SQLAlchemyEvaluacionActivaQueryRepository(session)
            resumen = await repo.listar_no_finalizadas()
            return any(
                item.evaluacion_id == uuid.UUID(context["evaluacion"]["id"]) for item in resumen
            )

    assert run_async(_verificar()) is False
