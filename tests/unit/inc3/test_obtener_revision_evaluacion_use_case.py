from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.errors import EvaluacionNoExiste, EvaluacionNoFinalizada
from src.actividad_evaluativa.entities.evaluacion import Evaluacion
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import DetalleCorreccionPregunta
from src.actividad_evaluativa.use_cases.obtener_revision_evaluacion import (
    AGGREGATE_TYPE_EVALUACION,
    ObtenerRevisionEvaluacionUseCase,
)
from tests.unit.inc3._fakes import FakeEventStore, FakePreguntaConsultaPort


async def _evaluacion_finalizada_con(
    event_store: FakeEventStore, preguntas_ids: list, respuestas: list[dict]
):
    """Arma una `Evaluacion` `Finalizada` con `preguntas_ids` asignadas y `respuestas` dadas.

    `respuestas` es una lista de dicts con `pregunta_id`, `contenido`, `es_correcta`,
    `ocurrido_en` (uno por cada `RespuestaRegistrada` a persistir, en orden).
    """
    actividad_id, estudiante_id = uuid4(), uuid4()
    evaluacion_id = Evaluacion.id_para(actividad_id, estudiante_id)
    eventos = [
        EventoParaAlmacenar(
            event_type="EvaluacionIniciada",
            payload={
                "evaluacion_id": str(evaluacion_id),
                "actividad_id": str(actividad_id),
                "estudiante_id": str(estudiante_id),
                "preguntas_asignadas": [
                    {"pregunta_id": str(pregunta_id), "orden": orden}
                    for orden, pregunta_id in enumerate(preguntas_ids)
                ],
                "ocurrido_en": "2026-01-01T00:00:00+00:00",
            },
        )
    ]
    for respuesta in respuestas:
        eventos.append(
            EventoParaAlmacenar(
                event_type="RespuestaRegistrada",
                payload={
                    "respuesta_id": str(uuid4()),
                    "evaluacion_id": str(evaluacion_id),
                    "pregunta_id": str(respuesta["pregunta_id"]),
                    "numero_intento": respuesta.get("numero_intento", 1),
                    "contenido": respuesta["contenido"],
                    "es_correcta": respuesta["es_correcta"],
                    "ocurrido_en": respuesta.get("ocurrido_en", "2026-01-01T01:00:00+00:00"),
                },
            )
        )
    eventos.append(
        EventoParaAlmacenar(
            event_type="EvaluacionFinalizada",
            payload={
                "evaluacion_id": str(evaluacion_id),
                "actor": "estudiante",
                "ocurrido_en": "2026-01-01T02:00:00+00:00",
            },
        )
    )
    await event_store.append(AGGREGATE_TYPE_EVALUACION, evaluacion_id, 0, eventos)
    return evaluacion_id, estudiante_id


class TestObtenerRevisionEvaluacionUseCase:
    async def test_revision_con_correctas_e_incorrectas(self):
        event_store = FakeEventStore()
        pregunta_correcta, pregunta_incorrecta = uuid4(), uuid4()
        evaluacion_id, estudiante_id = await _evaluacion_finalizada_con(
            event_store,
            [pregunta_correcta, pregunta_incorrecta],
            [
                {
                    "pregunta_id": pregunta_correcta,
                    "contenido": {"opcion_indice": 0},
                    "es_correcta": True,
                },
                {
                    "pregunta_id": pregunta_incorrecta,
                    "contenido": {"opcion_indice": 1},
                    "es_correcta": False,
                },
            ],
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.detalles[pregunta_correcta] = DetalleCorreccionPregunta(
            texto="¿Correcta?", contenido_correcto={"opcion_indice": 0}
        )
        pregunta_consulta.detalles[pregunta_incorrecta] = DetalleCorreccionPregunta(
            texto="¿Incorrecta?", contenido_correcto={"opcion_indice": 0}
        )
        use_case = ObtenerRevisionEvaluacionUseCase(pregunta_consulta, event_store)

        revision = await use_case.execute(evaluacion_id, estudiante_id)

        assert revision.cantidad_preguntas == 2
        assert revision.cantidad_correctas == 1
        assert revision.cantidad_incorrectas == 1

        fila_correcta = next(f for f in revision.detalle if f.pregunta_id == pregunta_correcta)
        assert fila_correcta.respondida is True
        assert fila_correcta.es_correcta is True
        assert fila_correcta.contenido_propio == {"opcion_indice": 0}
        assert fila_correcta.contenido_correcto is None

        fila_incorrecta = next(f for f in revision.detalle if f.pregunta_id == pregunta_incorrecta)
        assert fila_incorrecta.respondida is True
        assert fila_incorrecta.es_correcta is False
        assert fila_incorrecta.contenido_propio == {"opcion_indice": 1}
        assert fila_incorrecta.contenido_correcto == {"opcion_indice": 0}

    async def test_pregunta_no_respondida_cuenta_como_incorrecta(self):
        event_store = FakeEventStore()
        pregunta_id = uuid4()
        evaluacion_id, estudiante_id = await _evaluacion_finalizada_con(
            event_store, [pregunta_id], []
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.detalles[pregunta_id] = DetalleCorreccionPregunta(
            texto="¿Sin responder?", contenido_correcto={"valor": True}
        )
        use_case = ObtenerRevisionEvaluacionUseCase(pregunta_consulta, event_store)

        revision = await use_case.execute(evaluacion_id, estudiante_id)

        assert revision.cantidad_correctas == 0
        assert revision.cantidad_incorrectas == 1
        fila = revision.detalle[0]
        assert fila.respondida is False
        assert fila.es_correcta is False
        assert fila.contenido_propio is None
        assert fila.contenido_correcto == {"valor": True}

    async def test_usa_la_respuesta_vigente_ante_reintentos(self):
        event_store = FakeEventStore()
        pregunta_id = uuid4()
        evaluacion_id, estudiante_id = await _evaluacion_finalizada_con(
            event_store,
            [pregunta_id],
            [
                {
                    "pregunta_id": pregunta_id,
                    "contenido": {"opcion_indice": 1},
                    "es_correcta": False,
                    "numero_intento": 1,
                    "ocurrido_en": "2026-01-01T01:00:00+00:00",
                },
                {
                    "pregunta_id": pregunta_id,
                    "contenido": {"opcion_indice": 0},
                    "es_correcta": True,
                    "numero_intento": 2,
                    "ocurrido_en": "2026-01-01T01:05:00+00:00",
                },
            ],
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.detalles[pregunta_id] = DetalleCorreccionPregunta(
            texto="¿Con reintento?", contenido_correcto={"opcion_indice": 0}
        )
        use_case = ObtenerRevisionEvaluacionUseCase(pregunta_consulta, event_store)

        revision = await use_case.execute(evaluacion_id, estudiante_id)

        fila = revision.detalle[0]
        assert fila.es_correcta is True
        assert fila.contenido_propio == {"opcion_indice": 0}
        assert fila.contenido_correcto is None

    async def test_rechaza_evaluacion_inexistente(self):
        event_store = FakeEventStore()
        pregunta_consulta = FakePreguntaConsultaPort()
        use_case = ObtenerRevisionEvaluacionUseCase(pregunta_consulta, event_store)

        with pytest.raises(EvaluacionNoExiste):
            await use_case.execute(uuid4(), uuid4())

    async def test_rechaza_evaluacion_de_otro_estudiante(self):
        event_store = FakeEventStore()
        evaluacion_id, _estudiante_id = await _evaluacion_finalizada_con(event_store, [uuid4()], [])
        pregunta_consulta = FakePreguntaConsultaPort()
        use_case = ObtenerRevisionEvaluacionUseCase(pregunta_consulta, event_store)

        with pytest.raises(EvaluacionNoExiste):
            await use_case.execute(evaluacion_id, uuid4())

    async def test_rechaza_evaluacion_en_curso(self):
        actividad_id, estudiante_id, pregunta_id = uuid4(), uuid4(), uuid4()
        evaluacion_id = Evaluacion.id_para(actividad_id, estudiante_id)
        event_store = FakeEventStore()
        await event_store.append(
            AGGREGATE_TYPE_EVALUACION,
            evaluacion_id,
            0,
            [
                EventoParaAlmacenar(
                    event_type="EvaluacionIniciada",
                    payload={
                        "evaluacion_id": str(evaluacion_id),
                        "actividad_id": str(actividad_id),
                        "estudiante_id": str(estudiante_id),
                        "preguntas_asignadas": [{"pregunta_id": str(pregunta_id), "orden": 0}],
                        "ocurrido_en": "2026-01-01T00:00:00+00:00",
                    },
                )
            ],
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        use_case = ObtenerRevisionEvaluacionUseCase(pregunta_consulta, event_store)

        with pytest.raises(EvaluacionNoFinalizada):
            await use_case.execute(evaluacion_id, estudiante_id)

    async def test_rechaza_evaluacion_suspendida(self):
        actividad_id, estudiante_id, pregunta_id = uuid4(), uuid4(), uuid4()
        evaluacion_id = Evaluacion.id_para(actividad_id, estudiante_id)
        event_store = FakeEventStore()
        await event_store.append(
            AGGREGATE_TYPE_EVALUACION,
            evaluacion_id,
            0,
            [
                EventoParaAlmacenar(
                    event_type="EvaluacionIniciada",
                    payload={
                        "evaluacion_id": str(evaluacion_id),
                        "actividad_id": str(actividad_id),
                        "estudiante_id": str(estudiante_id),
                        "preguntas_asignadas": [{"pregunta_id": str(pregunta_id), "orden": 0}],
                        "ocurrido_en": "2026-01-01T00:00:00+00:00",
                    },
                ),
                EventoParaAlmacenar(
                    event_type="EvaluacionSuspendida",
                    payload={
                        "evaluacion_id": str(evaluacion_id),
                        "actor": "estudiante",
                        "ocurrido_en": "2026-01-01T00:30:00+00:00",
                    },
                ),
            ],
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        use_case = ObtenerRevisionEvaluacionUseCase(pregunta_consulta, event_store)

        with pytest.raises(EvaluacionNoFinalizada):
            await use_case.execute(evaluacion_id, estudiante_id)
