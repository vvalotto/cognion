"""Steps BDD de US-4.1.1 (`tests/features/inc4/US-4.1.1-infra-consulta-analytics.feature`)."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.analytics.frameworks.adapters.evaluacion_desempeno_consulta_port_in_process import (
    EvaluacionDesempenoConsultaPortInProcess,
)
from src.shared.frameworks.db import SessionLocal

scenarios("../../features/inc4/US-4.1.1-infra-consulta-analytics.feature")

AGGREGATE_TYPE_EVALUACION = "Evaluacion"
AGGREGATE_TYPE_ACTIVIDAD = "ActividadEvaluativaPeriodoAbierto"


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_analytics():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {"estudiante_id": uuid4(), "materia_id": uuid4(), "esperado": {}}


async def _crear_actividad(store: SQLAlchemyEventStore, actividad_id, materia_id) -> None:
    await store.append(
        AGGREGATE_TYPE_ACTIVIDAD,
        actividad_id,
        0,
        [
            EventoParaAlmacenar(
                "ActividadEvaluativaCreada",
                {"actividad_id": str(actividad_id), "materia_id": str(materia_id)},
            )
        ],
    )


async def _iniciar_evaluacion(
    store: SQLAlchemyEventStore, evaluacion_id, actividad_id, estudiante_id
) -> int:
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        0,
        [
            EventoParaAlmacenar(
                "EvaluacionIniciada",
                {
                    "evaluacion_id": str(evaluacion_id),
                    "actividad_id": str(actividad_id),
                    "estudiante_id": str(estudiante_id),
                },
            )
        ],
    )
    return 1


async def _registrar_respuesta(
    store: SQLAlchemyEventStore, evaluacion_id, seq: int, pregunta_id, es_correcta: bool
) -> int:
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        seq,
        [
            EventoParaAlmacenar(
                "RespuestaRegistrada",
                {
                    "respuesta_id": str(uuid4()),
                    "evaluacion_id": str(evaluacion_id),
                    "pregunta_id": str(pregunta_id),
                    "numero_intento": 1,
                    "contenido": {},
                    "es_correcta": es_correcta,
                },
            )
        ],
    )
    return seq + 1


async def _finalizar_evaluacion(store: SQLAlchemyEventStore, evaluacion_id, seq: int) -> int:
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        seq,
        [EventoParaAlmacenar("EvaluacionFinalizada", {"evaluacion_id": str(evaluacion_id), "actor": "estudiante"})],
    )
    return seq + 1


async def _crear_evaluacion_finalizada(
    store: SQLAlchemyEventStore, actividad_id, estudiante_id, correctas: int, incorrectas: int
):
    evaluacion_id = uuid4()
    seq = await _iniciar_evaluacion(store, evaluacion_id, actividad_id, estudiante_id)
    for _ in range(correctas):
        seq = await _registrar_respuesta(store, evaluacion_id, seq, uuid4(), True)
    for _ in range(incorrectas):
        seq = await _registrar_respuesta(store, evaluacion_id, seq, uuid4(), False)
    await _finalizar_evaluacion(store, evaluacion_id, seq)
    return evaluacion_id


@given(
    "un estudiante con 2 Evaluacion finalizadas en la materia X (una con 8 correctas y "
    "2 incorrectas, otra con 5 correctas y 3 incorrectas)"
)
def dos_evaluaciones_finalizadas_en_materia_x(context):
    async def _setup():
        async with SessionLocal() as session:
            store = SQLAlchemyEventStore(session)
            actividad_id = uuid4()
            await _crear_actividad(store, actividad_id, context["materia_id"])
            eval_1 = await _crear_evaluacion_finalizada(
                store, actividad_id, context["estudiante_id"], 8, 2
            )
            eval_2 = await _crear_evaluacion_finalizada(
                store, actividad_id, context["estudiante_id"], 5, 3
            )
            context["esperado"] = {eval_1: (8, 2), eval_2: (5, 3)}

    run_async(_setup())


@given("un estudiante con una Evaluacion EnCurso (sin EvaluacionFinalizada) en la materia X")
def evaluacion_en_curso_sin_finalizar(context):
    async def _setup():
        async with SessionLocal() as session:
            store = SQLAlchemyEventStore(session)
            actividad_id = uuid4()
            await _crear_actividad(store, actividad_id, context["materia_id"])
            evaluacion_id = uuid4()
            seq = await _iniciar_evaluacion(
                store, evaluacion_id, actividad_id, context["estudiante_id"]
            )
            await _registrar_respuesta(store, evaluacion_id, seq, uuid4(), True)

    run_async(_setup())


@given(
    "una Evaluacion finalizada con 2 Respuesta para la misma pregunta_id "
    "(la primera incorrecta, la segunda mas reciente correcta)"
)
def evaluacion_con_reintento_de_respuesta(context):
    async def _setup():
        async with SessionLocal() as session:
            store = SQLAlchemyEventStore(session)
            actividad_id = uuid4()
            await _crear_actividad(store, actividad_id, context["materia_id"])
            evaluacion_id = uuid4()
            pregunta_id = uuid4()
            seq = await _iniciar_evaluacion(
                store, evaluacion_id, actividad_id, context["estudiante_id"]
            )
            seq = await _registrar_respuesta(store, evaluacion_id, seq, pregunta_id, False)
            seq = await _registrar_respuesta(store, evaluacion_id, seq, pregunta_id, True)
            await _finalizar_evaluacion(store, evaluacion_id, seq)
            context["evaluacion_id"] = evaluacion_id

    run_async(_setup())


@given("un estudiante con Evaluacion finalizadas en dos materias distintas")
def evaluaciones_en_dos_materias_distintas(context):
    async def _setup():
        async with SessionLocal() as session:
            store = SQLAlchemyEventStore(session)
            actividad_x, actividad_y = uuid4(), uuid4()
            materia_y = uuid4()
            await _crear_actividad(store, actividad_x, context["materia_id"])
            await _crear_actividad(store, actividad_y, materia_y)
            eval_x = await _crear_evaluacion_finalizada(
                store, actividad_x, context["estudiante_id"], 3, 1
            )
            await _crear_evaluacion_finalizada(store, actividad_y, context["estudiante_id"], 2, 2)
            context["evaluacion_id_materia_x"] = eval_x

    run_async(_setup())


@given("un estudiante sin ninguna Evaluacion finalizada")
def estudiante_sin_evaluaciones(context):
    """Ninguna evaluación en el event store para este estudiante — no requiere setup."""


@when("se llama listar_evaluaciones_finalizadas(estudiante_id, materia_id=X)")
def llamar_listar_evaluaciones_finalizadas(context):
    async def _call():
        async with SessionLocal() as session:
            adapter = EvaluacionDesempenoConsultaPortInProcess(session)
            return await adapter.listar_evaluaciones_finalizadas(
                context["estudiante_id"], context["materia_id"]
            )

    context["resultado"] = run_async(_call())


@when("se llama listar_evaluaciones_finalizadas(estudiante_id, materia_id de esa Evaluacion)")
def llamar_listar_evaluaciones_finalizadas_materia_de_la_evaluacion(context):
    async def _call():
        async with SessionLocal() as session:
            adapter = EvaluacionDesempenoConsultaPortInProcess(session)
            return await adapter.listar_evaluaciones_finalizadas(
                context["estudiante_id"], context["materia_id"]
            )

    context["resultado"] = run_async(_call())


@then("el resultado tiene 2 filas con los conteos exactos de cada una")
def valida_dos_filas_con_conteos_exactos(context):
    resultado = context["resultado"]
    assert len(resultado) == 2
    por_id = {r.evaluacion_id: (r.cantidad_correctas, r.cantidad_incorrectas) for r in resultado}
    assert por_id == context["esperado"]


@then("esa Evaluacion no aparece en el resultado")
def valida_evaluacion_no_aparece(context):
    assert context["resultado"] == []


@then("esa pregunta cuenta como correcta, no como incorrecta")
def valida_pregunta_cuenta_como_correcta(context):
    resultado = context["resultado"]
    assert len(resultado) == 1
    assert resultado[0].evaluacion_id == context["evaluacion_id"]
    assert (resultado[0].cantidad_correctas, resultado[0].cantidad_incorrectas) == (1, 0)


@then("el resultado solo incluye las de la materia X")
def valida_resultado_solo_materia_x(context):
    resultado = context["resultado"]
    assert [r.evaluacion_id for r in resultado] == [context["evaluacion_id_materia_x"]]
    assert all(r.materia_id == context["materia_id"] for r in resultado)


@then("el resultado es una lista vacía")
def valida_resultado_vacio(context):
    assert context["resultado"] == []
