from datetime import UTC, datetime
from uuid import uuid4

from src.actividad_evaluativa.entities.evaluacion import (
    EstadoEvaluacion,
    Evaluacion,
    PreguntaAsignada,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventoAlmacenado


class TestIdPara:
    def test_es_determinista_para_el_mismo_par(self):
        actividad_id, estudiante_id = uuid4(), uuid4()

        id_1 = Evaluacion.id_para(actividad_id, estudiante_id)
        id_2 = Evaluacion.id_para(actividad_id, estudiante_id)

        assert id_1 == id_2

    def test_es_distinto_para_estudiantes_distintos(self):
        actividad_id = uuid4()

        id_estudiante_1 = Evaluacion.id_para(actividad_id, uuid4())
        id_estudiante_2 = Evaluacion.id_para(actividad_id, uuid4())

        assert id_estudiante_1 != id_estudiante_2

    def test_es_distinto_para_actividades_distintas(self):
        estudiante_id = uuid4()

        id_actividad_1 = Evaluacion.id_para(uuid4(), estudiante_id)
        id_actividad_2 = Evaluacion.id_para(uuid4(), estudiante_id)

        assert id_actividad_1 != id_actividad_2


class TestCrear:
    def test_crea_en_curso_con_id_determinista(self):
        actividad_id, estudiante_id = uuid4(), uuid4()
        preguntas = [PreguntaAsignada(pregunta_id=uuid4(), orden=0)]

        evaluacion = Evaluacion.crear(actividad_id, estudiante_id, preguntas)

        assert evaluacion.id == Evaluacion.id_para(actividad_id, estudiante_id)
        assert evaluacion.actividad_id == actividad_id
        assert evaluacion.estudiante_id == estudiante_id
        assert evaluacion.preguntas_asignadas == preguntas
        assert evaluacion.estado == EstadoEvaluacion.EN_CURSO


class TestReconstruir:
    def test_reconstruye_desde_el_evento_evaluacion_iniciada(self):
        evaluacion_id, actividad_id, estudiante_id = uuid4(), uuid4(), uuid4()
        pregunta_id = uuid4()
        ocurrido_en = datetime.now(UTC)
        evento = EventoAlmacenado(
            sequence_number=1,
            event_type="EvaluacionIniciada",
            payload={
                "evaluacion_id": str(evaluacion_id),
                "actividad_id": str(actividad_id),
                "estudiante_id": str(estudiante_id),
                "preguntas_asignadas": [{"pregunta_id": str(pregunta_id), "orden": 0}],
                "ocurrido_en": ocurrido_en.isoformat(),
            },
            occurred_at=ocurrido_en,
        )

        evaluacion = Evaluacion.reconstruir([evento])

        assert evaluacion.id == evaluacion_id
        assert evaluacion.actividad_id == actividad_id
        assert evaluacion.estudiante_id == estudiante_id
        assert evaluacion.preguntas_asignadas == [
            PreguntaAsignada(pregunta_id=pregunta_id, orden=0)
        ]
        assert evaluacion.estado == EstadoEvaluacion.EN_CURSO
        assert evaluacion.iniciada_en == ocurrido_en
