"""Tests unitarios de `_a_response` — enriquecimiento de `EvaluacionResponse` (`US-3.4.6`)."""

from uuid import uuid4

from src.actividad_evaluativa.entities.evaluacion import Evaluacion, PreguntaAsignada, Respuesta
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import ContenidoPregunta
from src.actividad_evaluativa.frameworks.api.evaluaciones_router import _a_response
from tests.unit.inc3._fakes import FakePreguntaConsultaPort


def _evaluacion(preguntas_asignadas: list[PreguntaAsignada]) -> Evaluacion:
    actividad_id, estudiante_id = uuid4(), uuid4()
    return Evaluacion.crear(actividad_id, estudiante_id, preguntas_asignadas)


class TestAResponse:
    async def test_enriquece_enunciado_y_opciones_de_opcion_multiple(self):
        pregunta_id = uuid4()
        evaluacion = _evaluacion([PreguntaAsignada(pregunta_id=pregunta_id, orden=0)])
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.contenidos[pregunta_id] = ContenidoPregunta(
            texto="¿Cuál es un principio SOLID?", opciones=["Responsabilidad única", "Otra"]
        )

        response = await _a_response(evaluacion, pregunta_consulta)

        assert len(response.preguntas_asignadas) == 1
        asignada = response.preguntas_asignadas[0]
        assert asignada.pregunta_id == pregunta_id
        assert asignada.enunciado == "¿Cuál es un principio SOLID?"
        assert asignada.opciones == ["Responsabilidad única", "Otra"]

    async def test_opciones_none_para_verdadero_falso(self):
        pregunta_id = uuid4()
        evaluacion = _evaluacion([PreguntaAsignada(pregunta_id=pregunta_id, orden=0)])
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.contenidos[pregunta_id] = ContenidoPregunta(
            texto="Python es un lenguaje tipado dinámicamente.", opciones=None
        )

        response = await _a_response(evaluacion, pregunta_consulta)

        assert response.preguntas_asignadas[0].opciones is None

    async def test_ninguna_opcion_expone_cual_es_correcta(self):
        """`ContenidoPregunta.opciones` es una lista de textos — sin flag de corrección."""
        pregunta_id = uuid4()
        evaluacion = _evaluacion([PreguntaAsignada(pregunta_id=pregunta_id, orden=0)])
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.contenidos[pregunta_id] = ContenidoPregunta(
            texto="Enunciado", opciones=["Opción A", "Opción B"]
        )

        response = await _a_response(evaluacion, pregunta_consulta)

        assert response.preguntas_asignadas[0].opciones == ["Opción A", "Opción B"]
        assert all(isinstance(o, str) for o in response.preguntas_asignadas[0].opciones)

    async def test_preguntas_respondidas_vacia_sin_respuestas(self):
        evaluacion = _evaluacion([PreguntaAsignada(pregunta_id=uuid4(), orden=0)])

        response = await _a_response(evaluacion, FakePreguntaConsultaPort())

        assert response.preguntas_respondidas == []

    async def test_preguntas_respondidas_incluye_ids_con_respuesta_confirmada(self):
        pregunta_id_1, pregunta_id_2 = uuid4(), uuid4()
        evaluacion = _evaluacion(
            [
                PreguntaAsignada(pregunta_id=pregunta_id_1, orden=0),
                PreguntaAsignada(pregunta_id=pregunta_id_2, orden=1),
            ]
        )
        evaluacion.respuestas.append(
            Respuesta(
                id=uuid4(),
                pregunta_id=pregunta_id_1,
                numero_intento=1,
                contenido={"opcion_indice": 0},
                es_correcta=True,
            )
        )

        response = await _a_response(evaluacion, FakePreguntaConsultaPort())

        assert response.preguntas_respondidas == [pregunta_id_1]

    async def test_preguntas_respondidas_sin_duplicados_ante_reintentos(self):
        pregunta_id = uuid4()
        evaluacion = _evaluacion([PreguntaAsignada(pregunta_id=pregunta_id, orden=0)])
        evaluacion.respuestas.append(
            Respuesta(
                id=uuid4(),
                pregunta_id=pregunta_id,
                numero_intento=1,
                contenido={"opcion_indice": 0},
                es_correcta=False,
            )
        )
        evaluacion.respuestas.append(
            Respuesta(
                id=uuid4(),
                pregunta_id=pregunta_id,
                numero_intento=2,
                contenido={"opcion_indice": 1},
                es_correcta=True,
            )
        )

        response = await _a_response(evaluacion, FakePreguntaConsultaPort())

        assert response.preguntas_respondidas == [pregunta_id]

    async def test_respuestas_confirmadas_vacia_sin_respuestas(self):
        evaluacion = _evaluacion([PreguntaAsignada(pregunta_id=uuid4(), orden=0)])

        response = await _a_response(evaluacion, FakePreguntaConsultaPort())

        assert response.respuestas_confirmadas == []

    async def test_respuestas_confirmadas_trae_el_contenido_de_la_vigente(self):
        pregunta_id = uuid4()
        evaluacion = _evaluacion([PreguntaAsignada(pregunta_id=pregunta_id, orden=0)])
        evaluacion.respuestas.append(
            Respuesta(
                id=uuid4(),
                pregunta_id=pregunta_id,
                numero_intento=1,
                contenido={"opcion_indice": 0},
                es_correcta=False,
            )
        )

        response = await _a_response(evaluacion, FakePreguntaConsultaPort())

        assert len(response.respuestas_confirmadas) == 1
        confirmada = response.respuestas_confirmadas[0]
        assert confirmada.pregunta_id == pregunta_id
        assert confirmada.contenido == {"opcion_indice": 0}

    async def test_respuestas_confirmadas_trae_solo_la_vigente_ante_reintentos(self):
        pregunta_id = uuid4()
        evaluacion = _evaluacion([PreguntaAsignada(pregunta_id=pregunta_id, orden=0)])
        evaluacion.respuestas.append(
            Respuesta(
                id=uuid4(),
                pregunta_id=pregunta_id,
                numero_intento=1,
                contenido={"opcion_indice": 0},
                es_correcta=False,
            )
        )
        evaluacion.respuestas.append(
            Respuesta(
                id=uuid4(),
                pregunta_id=pregunta_id,
                numero_intento=2,
                contenido={"opcion_indice": 1},
                es_correcta=True,
            )
        )

        response = await _a_response(evaluacion, FakePreguntaConsultaPort())

        assert len(response.respuestas_confirmadas) == 1
        assert response.respuestas_confirmadas[0].contenido == {"opcion_indice": 1}

    async def test_respuestas_confirmadas_no_expone_es_correcta(self):
        respuesta = Respuesta(
            id=uuid4(),
            pregunta_id=uuid4(),
            numero_intento=1,
            contenido={"valor": True},
            es_correcta=True,
        )
        evaluacion = _evaluacion([PreguntaAsignada(pregunta_id=respuesta.pregunta_id, orden=0)])
        evaluacion.respuestas.append(respuesta)

        response = await _a_response(evaluacion, FakePreguntaConsultaPort())

        assert not hasattr(response.respuestas_confirmadas[0], "es_correcta")

    async def test_preserva_el_resto_de_los_campos_de_evaluacion(self):
        pregunta_id = uuid4()
        evaluacion = _evaluacion([PreguntaAsignada(pregunta_id=pregunta_id, orden=0)])

        response = await _a_response(evaluacion, FakePreguntaConsultaPort())

        assert response.id == evaluacion.id
        assert response.actividad_id == evaluacion.actividad_id
        assert response.estudiante_id == evaluacion.estudiante_id
        assert response.estado == evaluacion.estado.value
        assert response.iniciada_en == evaluacion.iniciada_en
