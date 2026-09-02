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

scenarios("../../features/inc3/US-3.1.3-iniciar-evaluacion.feature")


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


async def _contar_eventos_evaluacion(evaluacion_id: str) -> int:
    async with SessionLocal() as session:
        resultado = await session.execute(
            text(
                "SELECT count(*) FROM events "
                "WHERE aggregate_type = 'Evaluacion' AND aggregate_id = :id"
            ),
            {"id": evaluacion_id},
        )
        return resultado.scalar_one()


async def _crear_materia_con_preguntas(cantidad: int) -> str:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        creada = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=docente_headers()
        )
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
    materia_id: str,
    cantidad_preguntas: int,
    fecha_apertura: datetime,
    fecha_cierre: datetime,
) -> str:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/actividades",
            json={
                "materia_id": materia_id,
                "fecha_apertura": fecha_apertura.isoformat(),
                "fecha_cierre": fecha_cierre.isoformat(),
                "cantidad_preguntas": cantidad_preguntas,
                "cantidad_intentos_permitidos": 1,
            },
            headers=docente_headers(),
        )
        return response.json()["id"]


async def _post_iniciar_evaluacion(actividad_id: str, estudiante_headers: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            "/evaluaciones", json={"actividad_id": actividad_id}, headers=estudiante_headers
        )


def _periodo_vigente() -> tuple[datetime, datetime]:
    apertura = datetime.now(UTC) - timedelta(days=1)
    return apertura, apertura + timedelta(days=7)


@given(
    parsers.parse(
        "una ActividadEvaluativaPeriodoAbierto vigente con cantidad_preguntas={cantidad:d}"
    )
)
def actividad_vigente_con_cantidad(context, cantidad):
    materia_id = run_async(_crear_materia_con_preguntas(cantidad + 10))
    apertura, cierre = _periodo_vigente()
    context["cantidad_preguntas"] = cantidad
    context["actividad_id"] = run_async(_crear_actividad(materia_id, cantidad, apertura, cierre))


@given(
    "una ActividadEvaluativaPeriodoAbierto vigente con más preguntas activas que cantidad_preguntas"
)
def actividad_vigente_con_banco_amplio(context):
    materia_id = run_async(_crear_materia_con_preguntas(20))
    apertura, cierre = _periodo_vigente()
    context["cantidad_preguntas"] = 5
    context["actividad_id"] = run_async(_crear_actividad(materia_id, 5, apertura, cierre))


@given("una ActividadEvaluativaPeriodoAbierto con fecha_apertura futura")
def actividad_con_apertura_futura(context):
    materia_id = run_async(_crear_materia_con_preguntas(20))
    apertura = datetime.now(UTC) + timedelta(days=1)
    cierre = apertura + timedelta(days=7)
    context["actividad_id"] = run_async(_crear_actividad(materia_id, 10, apertura, cierre))


@given("una ActividadEvaluativaPeriodoAbierto con fecha_cierre pasada")
def actividad_con_cierre_pasado(context):
    materia_id = run_async(_crear_materia_con_preguntas(20))
    cierre = datetime.now(UTC) - timedelta(days=1)
    apertura = cierre - timedelta(days=7)
    context["actividad_id"] = run_async(_crear_actividad(materia_id, 10, apertura, cierre))


@given("un Estudiante autenticado sin Evaluacion previa para esa actividad")
def estudiante_autenticado_sin_evaluacion_previa(context):
    estudiante_id, headers = run_async(crear_estudiante())
    context["estudiante_id"] = estudiante_id
    context["estudiante_headers"] = headers


@given("una Evaluacion EnCurso ya existente para (actividad_id, estudiante_id)")
def evaluacion_en_curso_existente(context):
    materia_id = run_async(_crear_materia_con_preguntas(20))
    apertura, cierre = _periodo_vigente()
    context["actividad_id"] = run_async(_crear_actividad(materia_id, 10, apertura, cierre))

    estudiante_id, headers = run_async(crear_estudiante())
    context["estudiante_id"] = estudiante_id
    context["estudiante_headers"] = headers
    context["response"] = run_async(_post_iniciar_evaluacion(context["actividad_id"], headers))
    context["evaluacion_original"] = context["response"].json()


@when("ejecuta IniciarEvaluacion(actividad_id, estudiante_id)")
def ejecuta_iniciar_evaluacion(context):
    context["response"] = run_async(
        _post_iniciar_evaluacion(context["actividad_id"], context["estudiante_headers"])
    )


@when("el mismo Estudiante ejecuta IniciarEvaluacion(actividad_id, estudiante_id) de nuevo")
def el_mismo_estudiante_ejecuta_de_nuevo(context):
    context["response"] = run_async(
        _post_iniciar_evaluacion(context["actividad_id"], context["estudiante_headers"])
    )


@when("dos Estudiantes distintos ejecutan IniciarEvaluacion cada uno por su cuenta")
def dos_estudiantes_ejecutan_iniciar_evaluacion(context):
    _id_1, headers_1 = run_async(crear_estudiante())
    _id_2, headers_2 = run_async(crear_estudiante())
    context["response_1"] = run_async(_post_iniciar_evaluacion(context["actividad_id"], headers_1))
    context["response_2"] = run_async(_post_iniciar_evaluacion(context["actividad_id"], headers_2))


@when("un Estudiante ejecuta IniciarEvaluacion(actividad_id, estudiante_id)")
def un_estudiante_ejecuta_iniciar_evaluacion(context):
    _estudiante_id, headers = run_async(crear_estudiante())
    context["response"] = run_async(_post_iniciar_evaluacion(context["actividad_id"], headers))


@when("un Estudiante sin Evaluacion previa ejecuta IniciarEvaluacion(actividad_id, estudiante_id)")
def estudiante_sin_evaluacion_previa_ejecuta(context):
    _estudiante_id, headers = run_async(crear_estudiante())
    context["response"] = run_async(_post_iniciar_evaluacion(context["actividad_id"], headers))


@then("el sistema crea una Evaluacion con estado EnCurso")
def valida_evaluacion_creada_en_curso(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["estado"] == "EnCurso"


@then(parsers.parse("preguntas_asignadas tiene exactamente {cantidad:d} PreguntaAsignada"))
def valida_cantidad_preguntas_asignadas(context, cantidad):
    assert len(context["response"].json()["preguntas_asignadas"]) == cantidad


@then("se emite el evento EvaluacionIniciada")
def valida_evento_emitido(context):
    evaluacion_id = context["response"].json()["id"]
    assert run_async(_contar_eventos_evaluacion(evaluacion_id)) == 1


@then("el sistema devuelve la misma Evaluacion existente")
def valida_devuelve_evaluacion_existente(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["id"] == context["evaluacion_original"]["id"]


@then("preguntas_asignadas es idéntico al set original (mismo orden, mismas preguntas)")
def valida_set_identico_al_original(context):
    assert (
        context["response"].json()["preguntas_asignadas"]
        == context["evaluacion_original"]["preguntas_asignadas"]
    )


@then("no se emite un nuevo evento EvaluacionIniciada")
def valida_no_se_emite_nuevo_evento(context):
    evaluacion_id = context["response"].json()["id"]
    assert run_async(_contar_eventos_evaluacion(evaluacion_id)) == 1


@then("cada uno recibe su propia Evaluacion con un set de preguntas propio")
def valida_cada_uno_recibe_evaluacion_propia(context):
    datos_1 = context["response_1"].json()
    datos_2 = context["response_2"].json()
    assert datos_1["id"] != datos_2["id"]
    assert datos_1["estudiante_id"] != datos_2["estudiante_id"]


@then("el sistema rechaza la operación con FueraDePeriodo")
def valida_rechazo_fuera_de_periodo(context):
    assert context["response"].status_code == 422
