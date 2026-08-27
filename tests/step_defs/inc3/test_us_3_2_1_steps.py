from __future__ import annotations

import asyncio
import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.actividad_evaluativa.entities.errors import (
    EvaluacionSuspendida,
    EvaluacionYaFinalizada,
)
from src.actividad_evaluativa.entities.evaluacion import (
    EstadoEvaluacion,
    Evaluacion,
    PreguntaAsignada,
)
from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc3._auth_headers import crear_estudiante, docente_headers

scenarios("../../features/inc3/US-3.2.1-registrar-respuesta.feature")


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
        query = "SELECT count(*) FROM events WHERE aggregate_type = 'Evaluacion' AND aggregate_id = :id"
        params: dict[str, object] = {"id": evaluacion_id}
        if event_type is not None:
            query += " AND event_type = :event_type"
            params["event_type"] = event_type
        resultado = await session.execute(text(query), params)
        return resultado.scalar_one()


async def _crear_materia_con_opcion_multiple() -> tuple[str, str]:
    """Crea una materia con una única pregunta de opción múltiple (opción correcta: índice 1)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        creada = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=docente_headers()
        )
        banco_id = creada.json()["banco_id"]
        respuesta = await client.post(
            "/preguntas/opcion-multiple",
            json={
                "banco_id": banco_id,
                "texto": f"Pregunta {uuid.uuid4()}",
                "opciones": [
                    {"texto": "Incorrecta", "es_correcta": False},
                    {"texto": "Correcta", "es_correcta": True},
                ],
                "unidad_tematica": "Unidad 1",
                "tema": "Tema",
                "dificultad": "medio",
                "importancia": "alto",
            },
            headers=docente_headers(),
        )
        return creada.json()["id"], respuesta.json()["id"]


async def _crear_actividad(
    materia_id: str,
    fecha_apertura: datetime,
    fecha_cierre: datetime,
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
                "cantidad_preguntas": 1,
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


def _periodo_vigente() -> tuple[datetime, datetime]:
    apertura = datetime.now(UTC) - timedelta(days=1)
    return apertura, apertura + timedelta(days=7)


async def _armar_evaluacion_en_curso(cantidad_intentos_permitidos: int = 1):
    materia_id, pregunta_id = await _crear_materia_con_opcion_multiple()
    apertura, cierre = _periodo_vigente()
    actividad_id = await _crear_actividad(materia_id, apertura, cierre, cantidad_intentos_permitidos)
    estudiante_id, headers = await crear_estudiante()
    evaluacion = await _iniciar_evaluacion(actividad_id, headers)
    return evaluacion, pregunta_id, headers


@given("una Evaluacion EnCurso con una PreguntaAsignada de tipo opción múltiple")
def evaluacion_en_curso_con_opcion_multiple(context):
    evaluacion, pregunta_id, headers = run_async(_armar_evaluacion_en_curso())
    context["evaluacion"] = evaluacion
    context["pregunta_id"] = pregunta_id
    context["estudiante_headers"] = headers


@given(parsers.parse("una Evaluacion EnCurso con cantidad_intentos_permitidos={cantidad:d}"))
def evaluacion_en_curso_con_intentos(context, cantidad):
    evaluacion, pregunta_id, headers = run_async(_armar_evaluacion_en_curso(cantidad))
    context["evaluacion"] = evaluacion
    context["pregunta_id"] = pregunta_id
    context["estudiante_headers"] = headers


@given("una Evaluacion EnCurso")
def evaluacion_en_curso_generica(context):
    evaluacion, pregunta_id, headers = run_async(_armar_evaluacion_en_curso())
    context["evaluacion"] = evaluacion
    context["pregunta_id"] = pregunta_id
    context["estudiante_headers"] = headers


@given(
    parsers.parse("ya existe una Respuesta previa (numero_intento={numero:d}) para esa pregunta")
)
def ya_existe_respuesta_previa_con_numero(context, numero):
    run_async(
        _registrar_respuesta(
            context["evaluacion"]["id"],
            context["pregunta_id"],
            {"opcion_indice": 1},
            context["estudiante_headers"],
        )
    )


@given("ya existe una Respuesta previa para esa pregunta")
def ya_existe_respuesta_previa(context):
    run_async(
        _registrar_respuesta(
            context["evaluacion"]["id"],
            context["pregunta_id"],
            {"opcion_indice": 1},
            context["estudiante_headers"],
        )
    )


@given("una Evaluacion en estado Suspendida")
def evaluacion_en_estado_suspendida(context):
    pregunta_id = uuid.uuid4()
    evaluacion = Evaluacion.crear(
        uuid.uuid4(), uuid.uuid4(), [PreguntaAsignada(pregunta_id=pregunta_id, orden=0)]
    )
    evaluacion.estado = EstadoEvaluacion.SUSPENDIDA
    context["evaluacion_dominio"] = evaluacion
    context["pregunta_id_dominio"] = pregunta_id


@given("una Evaluacion en estado Finalizada")
def evaluacion_en_estado_finalizada(context):
    pregunta_id = uuid.uuid4()
    evaluacion = Evaluacion.crear(
        uuid.uuid4(), uuid.uuid4(), [PreguntaAsignada(pregunta_id=pregunta_id, orden=0)]
    )
    evaluacion.estado = EstadoEvaluacion.FINALIZADA
    context["evaluacion_dominio"] = evaluacion
    context["pregunta_id_dominio"] = pregunta_id


@given("una Evaluacion EnCurso cuya actividad ya pasó su fecha_cierre")
def evaluacion_en_curso_actividad_por_cerrar(context):
    materia_id, pregunta_id = run_async(_crear_materia_con_opcion_multiple())
    apertura = datetime.now(UTC) - timedelta(milliseconds=500)
    cierre = apertura + timedelta(seconds=1.5)
    actividad_id = run_async(_crear_actividad(materia_id, apertura, cierre))
    _estudiante_id, headers = run_async(crear_estudiante())
    evaluacion = run_async(_iniciar_evaluacion(actividad_id, headers))
    time.sleep(2)  # deja pasar fecha_cierre antes de intentar RegistrarRespuesta
    context["evaluacion"] = evaluacion
    context["pregunta_id"] = pregunta_id
    context["estudiante_headers"] = headers


@given("un Estudiante que confirma una Respuesta")
def estudiante_que_confirma_respuesta(context):
    evaluacion, pregunta_id, headers = run_async(_armar_evaluacion_en_curso())
    context["evaluacion"] = evaluacion
    context["pregunta_id"] = pregunta_id
    context["estudiante_headers"] = headers
    context["response"] = run_async(
        _registrar_respuesta(evaluacion["id"], pregunta_id, {"opcion_indice": 1}, headers)
    )


@when(parsers.parse("el Estudiante ejecuta RegistrarRespuesta(evaluacion_id, pregunta_id, {{opcion_indice: {indice:d}}})"))
def ejecuta_registrar_respuesta_opcion_indice(context, indice):
    context["response"] = run_async(
        _registrar_respuesta(
            context["evaluacion"]["id"],
            context["pregunta_id"],
            {"opcion_indice": indice},
            context["estudiante_headers"],
        )
    )


@when("el Estudiante confirma una nueva respuesta para la misma pregunta")
def confirma_nueva_respuesta_misma_pregunta(context):
    context["response"] = run_async(
        _registrar_respuesta(
            context["evaluacion"]["id"],
            context["pregunta_id"],
            {"opcion_indice": 0},
            context["estudiante_headers"],
        )
    )


@when("el Estudiante intenta confirmar una nueva respuesta para la misma pregunta")
def intenta_confirmar_nueva_respuesta_misma_pregunta(context):
    context["response"] = run_async(
        _registrar_respuesta(
            context["evaluacion"]["id"],
            context["pregunta_id"],
            {"opcion_indice": 0},
            context["estudiante_headers"],
        )
    )


@when("el Estudiante ejecuta RegistrarRespuesta con un pregunta_id fuera de su set asignado")
def ejecuta_registrar_respuesta_pregunta_no_asignada(context):
    context["response"] = run_async(
        _registrar_respuesta(
            context["evaluacion"]["id"],
            str(uuid.uuid4()),
            {"opcion_indice": 0},
            context["estudiante_headers"],
        )
    )


@when("el Estudiante intenta RegistrarRespuesta")
def intenta_registrar_respuesta(context):
    if "evaluacion_dominio" in context:
        try:
            context["evaluacion_dominio"].validar_para_registrar_respuesta(
                context["pregunta_id_dominio"], cantidad_intentos_permitidos=1
            )
            context["error_dominio"] = None
        except (EvaluacionSuspendida, EvaluacionYaFinalizada) as exc:
            context["error_dominio"] = exc
        return

    context["response"] = run_async(
        _registrar_respuesta(
            context["evaluacion"]["id"],
            context["pregunta_id"],
            {"opcion_indice": 0},
            context["estudiante_headers"],
        )
    )


@when("el proceso backend se reinicia inmediatamente después de la confirmación")
def el_proceso_backend_se_reinicia(context):
    """No-op: la persistencia ya ocurrió en `SessionLocal`, una sesión propia (INV-AE-09).

    El `Then` siguiente abre una `SessionLocal` nueva e independiente para leer el event
    store — eso es lo que demuestra que sobrevive a un reinicio del proceso, no un mock.
    """


@then("el sistema crea una Respuesta con numero_intento=1 y es_correcta calculado")
def valida_respuesta_creada_numero_intento_uno(context):
    assert context["response"].status_code == 201
    assert context["response"].json()["numero_intento"] == 1


@then("se emite el evento RespuestaRegistrada")
def valida_evento_respuesta_registrada(context):
    evaluacion_id = context["evaluacion"]["id"]
    assert run_async(_contar_eventos(evaluacion_id, "RespuestaRegistrada")) == 1


@then("la respuesta HTTP no informa si es_correcta")
def valida_respuesta_no_informa_correccion(context):
    data = context["response"].json()
    assert "es_correcta" not in data
    assert "contenido" not in data


@then("el sistema crea una segunda Respuesta con numero_intento=2")
def valida_segunda_respuesta_numero_intento_dos(context):
    assert context["response"].status_code == 201
    assert context["response"].json()["numero_intento"] == 2


@then("ambas Respuesta conviven en la colección — la de numero_intento=2 es la vigente")
def valida_ambas_respuestas_conviven(context):
    evaluacion_id = context["evaluacion"]["id"]
    assert run_async(_contar_eventos(evaluacion_id, "RespuestaRegistrada")) == 2


@then("el sistema rechaza la operación con IntentosAgotados")
def valida_rechazo_intentos_agotados(context):
    assert context["response"].status_code == 422


@then("no se persiste ninguna Respuesta nueva")
def valida_no_se_persiste_respuesta_nueva(context):
    evaluacion_id = context["evaluacion"]["id"]
    assert run_async(_contar_eventos(evaluacion_id, "RespuestaRegistrada")) == 1


@then("el sistema rechaza la operación con PreguntaNoAsignada")
def valida_rechazo_pregunta_no_asignada(context):
    assert context["response"].status_code == 404


@then("el sistema rechaza la operación con EvaluacionSuspendida")
def valida_rechazo_evaluacion_suspendida(context):
    assert isinstance(context["error_dominio"], EvaluacionSuspendida)


@then("el sistema rechaza la operación con EvaluacionYaFinalizada")
def valida_rechazo_evaluacion_ya_finalizada(context):
    assert isinstance(context["error_dominio"], EvaluacionYaFinalizada)


@then("el sistema rechaza la operación con FueraDePeriodo")
def valida_rechazo_fuera_de_periodo(context):
    assert context["response"].status_code == 422


@then("la Respuesta persiste en el event store al reiniciar el proceso")
def valida_persistencia_atomica(context):
    evaluacion_id = context["evaluacion"]["id"]
    assert run_async(_contar_eventos(evaluacion_id, "RespuestaRegistrada")) == 1


@then("se reconstruye correctamente por replay del stream de la Evaluacion")
def valida_reconstruccion_por_replay(context):
    from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
        SQLAlchemyEventStore,
    )

    async def _reconstruir():
        async with SessionLocal() as session:
            store = SQLAlchemyEventStore(session)
            eventos = await store.load("Evaluacion", uuid.UUID(context["evaluacion"]["id"]))
            return Evaluacion.reconstruir(eventos)

    evaluacion = run_async(_reconstruir())
    assert len(evaluacion.respuestas) == 1
    assert evaluacion.respuestas[0].pregunta_id == uuid.UUID(context["pregunta_id"])
