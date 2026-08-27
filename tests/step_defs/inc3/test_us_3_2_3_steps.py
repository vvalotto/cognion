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

scenarios("../../features/inc3/US-3.2.3-finalizar-evaluacion-revision.feature")


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


async def _crear_materia_con_verdadero_falso(
    respuesta_correcta: bool = True, cantidad: int = 1
) -> tuple[str, list[str]]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        creada = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=docente_headers()
        )
        banco_id = creada.json()["banco_id"]
        ids = []
        for _ in range(cantidad):
            respuesta = await client.post(
                "/preguntas/verdadero-falso",
                json={
                    "banco_id": banco_id,
                    "texto": f"Pregunta {uuid.uuid4()}",
                    "respuesta_correcta": respuesta_correcta,
                    "unidad_tematica": "Unidad 1",
                    "tema": "Tema",
                    "dificultad": "medio",
                    "importancia": "alto",
                },
                headers=docente_headers(),
            )
            ids.append(respuesta.json()["id"])
        return creada.json()["id"], ids


async def _crear_actividad(
    materia_id: str,
    fecha_apertura: datetime,
    fecha_cierre: datetime,
    cantidad_preguntas: int = 1,
    cantidad_intentos_permitidos: int = 1,
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
                "cantidad_intentos_permitidos": cantidad_intentos_permitidos,
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


async def _registrar_respuesta(
    evaluacion_id: str, pregunta_id: str, contenido: dict, estudiante_headers: dict
):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            f"/evaluaciones/{evaluacion_id}/respuestas",
            json={"pregunta_id": pregunta_id, "contenido": contenido},
            headers=estudiante_headers,
        )


async def _finalizar(evaluacion_id: str, estudiante_headers: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            f"/evaluaciones/{evaluacion_id}/finalizar", headers=estudiante_headers
        )


async def _obtener_revision(evaluacion_id: str, estudiante_headers: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(
            f"/evaluaciones/{evaluacion_id}/revision", headers=estudiante_headers
        )


def _periodo_vigente() -> tuple[datetime, datetime]:
    apertura = datetime.now(UTC) - timedelta(days=1)
    return apertura, apertura + timedelta(days=7)


async def _armar_evaluacion_en_curso():
    materia_id, pregunta_ids = await _crear_materia_con_verdadero_falso()
    apertura, cierre = _periodo_vigente()
    actividad_id = await _crear_actividad(materia_id, apertura, cierre)
    _estudiante_id, headers = await crear_estudiante()
    evaluacion = await _iniciar_evaluacion(actividad_id, headers)
    return evaluacion, pregunta_ids[0], headers


@given("una Evaluacion EnCurso con algunas respuestas registradas")
def evaluacion_en_curso_con_respuestas(context):
    evaluacion, pregunta_id, headers = run_async(_armar_evaluacion_en_curso())
    run_async(_registrar_respuesta(evaluacion["id"], pregunta_id, {"valor": True}, headers))
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers


@given("una Evaluacion EnCurso")
def evaluacion_en_curso(context):
    evaluacion, _pregunta_id, headers = run_async(_armar_evaluacion_en_curso())
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers


@given("una Evaluacion Suspendida")
def evaluacion_suspendida(context):
    evaluacion, _pregunta_id, headers = run_async(_armar_evaluacion_en_curso())

    async def _suspender():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(f"/evaluaciones/{evaluacion['id']}/suspender", headers=headers)

    run_async(_suspender())
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers


@given("una Evaluacion Finalizada")
def evaluacion_finalizada(context):
    evaluacion, _pregunta_id, headers = run_async(_armar_evaluacion_en_curso())
    run_async(_finalizar(evaluacion["id"], headers))
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers


@given(
    "una Evaluacion Finalizada con 3 preguntas asignadas, "
    "2 respondidas correctamente y 1 incorrectamente"
)
def evaluacion_finalizada_con_correctas_e_incorrectas(context):
    async def _armar():
        materia_id, pregunta_ids = await _crear_materia_con_verdadero_falso(
            respuesta_correcta=True, cantidad=3
        )
        apertura, cierre = _periodo_vigente()
        actividad_id = await _crear_actividad(
            materia_id, apertura, cierre, cantidad_preguntas=3
        )
        _estudiante_id, headers = await crear_estudiante()
        evaluacion = await _iniciar_evaluacion(actividad_id, headers)
        asignadas = [p["pregunta_id"] for p in evaluacion["preguntas_asignadas"]]

        correctas = asignadas[:2]
        incorrecta = asignadas[2]
        for pregunta_id in correctas:
            await _registrar_respuesta(evaluacion["id"], pregunta_id, {"valor": True}, headers)
        await _registrar_respuesta(evaluacion["id"], incorrecta, {"valor": False}, headers)
        await _finalizar(evaluacion["id"], headers)
        return evaluacion, headers, correctas, incorrecta

    evaluacion, headers, correctas, incorrecta = run_async(_armar())
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers
    context["preguntas_correctas"] = correctas
    context["pregunta_incorrecta"] = incorrecta


@given("una Evaluacion Finalizada con una PreguntaAsignada sin ninguna Respuesta")
def evaluacion_finalizada_sin_responder(context):
    evaluacion, pregunta_id, headers = run_async(_armar_evaluacion_en_curso())
    run_async(_finalizar(evaluacion["id"], headers))
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers
    context["pregunta_id"] = pregunta_id


@given(
    "una Evaluacion Finalizada con 2 Respuesta para la misma pregunta, "
    "la primera incorrecta y la segunda (más reciente) correcta"
)
def evaluacion_finalizada_con_reintento(context):
    async def _armar():
        materia_id, pregunta_ids = await _crear_materia_con_verdadero_falso(
            respuesta_correcta=True, cantidad=1
        )
        apertura, cierre = _periodo_vigente()
        actividad_id = await _crear_actividad(
            materia_id, apertura, cierre, cantidad_intentos_permitidos=2
        )
        _estudiante_id, headers = await crear_estudiante()
        evaluacion = await _iniciar_evaluacion(actividad_id, headers)
        pregunta_id = pregunta_ids[0]
        await _registrar_respuesta(evaluacion["id"], pregunta_id, {"valor": False}, headers)
        await _registrar_respuesta(evaluacion["id"], pregunta_id, {"valor": True}, headers)
        await _finalizar(evaluacion["id"], headers)
        return evaluacion, headers, pregunta_id

    evaluacion, headers, pregunta_id = run_async(_armar())
    context["evaluacion"] = evaluacion
    context["estudiante_headers"] = headers
    context["pregunta_id"] = pregunta_id


@when("el Estudiante ejecuta FinalizarEvaluacion(evaluacion_id)")
def ejecuta_finalizar_evaluacion(context):
    context["response"] = run_async(
        _finalizar(context["evaluacion"]["id"], context["estudiante_headers"])
    )


@when("el Estudiante intenta FinalizarEvaluacion de nuevo")
def intenta_finalizar_de_nuevo(context):
    context["response"] = run_async(
        _finalizar(context["evaluacion"]["id"], context["estudiante_headers"])
    )


@when("el Estudiante ejecuta ObtenerRevisionEvaluacion(evaluacion_id)")
def ejecuta_obtener_revision(context):
    context["response"] = run_async(
        _obtener_revision(context["evaluacion"]["id"], context["estudiante_headers"])
    )


@when("el Estudiante intenta ObtenerRevisionEvaluacion")
def intenta_obtener_revision(context):
    context["response"] = run_async(
        _obtener_revision(context["evaluacion"]["id"], context["estudiante_headers"])
    )


@then("el estado pasa a Finalizada")
def valida_estado_finalizada(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["estado"] == "Finalizada"


@then("se emite el evento EvaluacionFinalizada")
def valida_evento_finalizada(context):
    evaluacion_id = context["evaluacion"]["id"]
    assert run_async(_contar_eventos(evaluacion_id, "EvaluacionFinalizada")) == 1


@then("el sistema rechaza la operación con EvaluacionYaFinalizada")
def valida_rechazo_evaluacion_ya_finalizada(context):
    assert context["response"].status_code == 422


@then("el sistema rechaza la operación con EvaluacionNoFinalizada")
def valida_rechazo_evaluacion_no_finalizada(context):
    assert context["response"].status_code == 422


@then("el sistema devuelve el detalle de las 3 preguntas")
def valida_devuelve_detalle_de_tres_preguntas(context):
    assert context["response"].status_code == 200
    cuerpo = context["response"].json()
    assert cuerpo["cantidad_preguntas"] == 3
    assert len(cuerpo["detalle"]) == 3


@then("la pregunta incorrecta incluye la respuesta correcta")
def valida_pregunta_incorrecta_incluye_correccion(context):
    cuerpo = context["response"].json()
    fila = next(
        f for f in cuerpo["detalle"] if f["pregunta_id"] == context["pregunta_incorrecta"]
    )
    assert fila["es_correcta"] is False
    assert fila["contenido_correcto"] is not None


@then("las preguntas correctas no incluyen la respuesta correcta")
def valida_preguntas_correctas_sin_correccion(context):
    cuerpo = context["response"].json()
    for pregunta_id in context["preguntas_correctas"]:
        fila = next(f for f in cuerpo["detalle"] if f["pregunta_id"] == pregunta_id)
        assert fila["es_correcta"] is True
        assert fila["contenido_correcto"] is None


@then("el resumen indica 2 correctas y 1 incorrecta sobre 3")
def valida_resumen_dos_correctas_una_incorrecta(context):
    cuerpo = context["response"].json()
    assert cuerpo["cantidad_correctas"] == 2
    assert cuerpo["cantidad_incorrectas"] == 1
    assert cuerpo["cantidad_preguntas"] == 3


@then("esa pregunta aparece con respondida = false")
def valida_pregunta_no_respondida(context):
    cuerpo = context["response"].json()
    fila = next(f for f in cuerpo["detalle"] if f["pregunta_id"] == context["pregunta_id"])
    assert fila["respondida"] is False


@then("cuenta como incorrecta en el resumen")
def valida_cuenta_como_incorrecta(context):
    cuerpo = context["response"].json()
    assert cuerpo["cantidad_incorrectas"] == 1
    assert cuerpo["cantidad_correctas"] == 0


@then("incluye la respuesta correcta")
def valida_incluye_respuesta_correcta(context):
    cuerpo = context["response"].json()
    fila = next(f for f in cuerpo["detalle"] if f["pregunta_id"] == context["pregunta_id"])
    assert fila["contenido_correcto"] is not None


@then("esa pregunta aparece como correcta con la respuesta más reciente")
def valida_pregunta_correcta_con_respuesta_reciente(context):
    cuerpo = context["response"].json()
    fila = next(f for f in cuerpo["detalle"] if f["pregunta_id"] == context["pregunta_id"])
    assert fila["es_correcta"] is True
    assert fila["contenido_propio"] == {"valor": True}
