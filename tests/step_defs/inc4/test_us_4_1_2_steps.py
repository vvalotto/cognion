"""Steps BDD de US-4.1.2 (`tests/features/inc4/US-4.1.2-desempeno-estudiante.feature`)."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer

scenarios("../../features/inc4/US-4.1.2-desempeno-estudiante.feature")

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
    return {"estudiante_id": uuid4(), "materia_id": uuid4()}


def _headers_estudiante(estudiante_id) -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(estudiante_id, TipoPerfil.ESTUDIANTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


def _headers_docente() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid4(), TipoPerfil.DOCENTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


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
    store: SQLAlchemyEventStore, evaluacion_id, seq: int, es_correcta: bool
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
                    "pregunta_id": str(uuid4()),
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
        [
            EventoParaAlmacenar(
                "EvaluacionFinalizada", {"evaluacion_id": str(evaluacion_id), "actor": "estudiante"}
            )
        ],
    )
    return seq + 1


async def _crear_evaluacion_finalizada(
    store: SQLAlchemyEventStore, actividad_id, estudiante_id, correctas: int, incorrectas: int
) -> None:
    evaluacion_id = uuid4()
    seq = await _iniciar_evaluacion(store, evaluacion_id, actividad_id, estudiante_id)
    for _ in range(correctas):
        seq = await _registrar_respuesta(store, evaluacion_id, seq, True)
    for _ in range(incorrectas):
        seq = await _registrar_respuesta(store, evaluacion_id, seq, False)
    await _finalizar_evaluacion(store, evaluacion_id, seq)


@given("un Estudiante autenticado con 2 Evaluacion finalizadas en la materia X")
def estudiante_con_dos_evaluaciones_finalizadas(context):
    async def _setup():
        async with SessionLocal() as session:
            store = SQLAlchemyEventStore(session)
            actividad_id = uuid4()
            await _crear_actividad(store, actividad_id, context["materia_id"])
            await _crear_evaluacion_finalizada(
                store, actividad_id, context["estudiante_id"], 8, 2
            )
            await _crear_evaluacion_finalizada(
                store, actividad_id, context["estudiante_id"], 5, 3
            )

    run_async(_setup())


@given("un Estudiante autenticado sin ninguna Evaluacion finalizada en la materia Y")
def estudiante_sin_evaluaciones_finalizadas(context):
    """Ninguna evaluación en el event store para este estudiante — no requiere setup."""


@given("una request sin JWT válido")
def request_sin_jwt(context):
    context["headers"] = None


@given("un Docente autenticado")
def docente_autenticado(context):
    context["headers"] = _headers_docente()


@given(
    "un Estudiante A autenticado y un Estudiante B con evaluaciones finalizadas en la materia X"
)
def estudiante_a_y_estudiante_b_con_evaluaciones(context):
    estudiante_b = uuid4()

    async def _setup():
        async with SessionLocal() as session:
            store = SQLAlchemyEventStore(session)
            actividad_id = uuid4()
            await _crear_actividad(store, actividad_id, context["materia_id"])
            await _crear_evaluacion_finalizada(store, actividad_id, estudiante_b, 9, 1)

    run_async(_setup())
    context["estudiante_b"] = estudiante_b


def _get(context, materia_id, headers) -> None:
    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(
                f"/analytics/materias/{materia_id}/mi-desempeno", headers=headers
            )

    context["response"] = run_async(_call())


@when("hace GET /analytics/materias/X/mi-desempeno")
def hace_get_materia_x(context):
    headers = context.get("headers", _headers_estudiante(context["estudiante_id"]))
    _get(context, context["materia_id"], headers)


@when("hace GET /analytics/materias/Y/mi-desempeno")
def hace_get_materia_y(context):
    _get(context, context["materia_id"], _headers_estudiante(context["estudiante_id"]))


@when("el Estudiante A hace GET /analytics/materias/X/mi-desempeno")
def estudiante_a_hace_get_materia_x(context):
    _get(context, context["materia_id"], _headers_estudiante(context["estudiante_id"]))


@then("recibe 200 con 2 filas en \"evaluaciones\" ordenadas por finalizada_en descendente")
def valida_200_con_dos_filas(context):
    response = context["response"]
    assert response.status_code == 200
    assert len(response.json()["evaluaciones"]) == 2


@then(
    "recibe el \"resumen\" acumulado correcto (total_correctas, total_incorrectas, "
    "porcentaje_acierto, cantidad_evaluaciones)"
)
def valida_resumen_acumulado(context):
    resumen = context["response"].json()["resumen"]
    assert resumen == {
        "total_correctas": 13,
        "total_incorrectas": 5,
        "porcentaje_acierto": 72,
        "cantidad_evaluaciones": 2,
    }


@then("recibe 200 con \"evaluaciones\": []")
def valida_200_evaluaciones_vacias(context):
    response = context["response"]
    assert response.status_code == 200
    assert response.json()["evaluaciones"] == []


@then("recibe \"resumen\" en cero, sin dividir por cero en porcentaje_acierto")
def valida_resumen_en_cero(context):
    resumen = context["response"].json()["resumen"]
    assert resumen == {
        "total_correctas": 0,
        "total_incorrectas": 0,
        "porcentaje_acierto": 0,
        "cantidad_evaluaciones": 0,
    }


@then("recibe 401")
def valida_401(context):
    assert context["response"].status_code == 401


@then("recibe 403")
def valida_403(context):
    assert context["response"].status_code == 403


@then("recibe únicamente su propio desempeño, nunca el del Estudiante B")
def valida_solo_propio_desempeno(context):
    response = context["response"]
    assert response.status_code == 200
    data = response.json()
    assert data["evaluaciones"] == []
    assert data["resumen"]["cantidad_evaluaciones"] == 0
