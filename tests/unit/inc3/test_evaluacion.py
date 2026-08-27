from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.errors import (
    EvaluacionNoSuspendida,
    EvaluacionSuspendida,
    EvaluacionYaFinalizada,
    EvaluacionYaSuspendida,
    IntentosAgotados,
    PreguntaNoAsignada,
)
from src.actividad_evaluativa.entities.evaluacion import (
    EstadoEvaluacion,
    Evaluacion,
    PreguntaAsignada,
    Respuesta,
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
        assert evaluacion.respuestas == []

    def test_reconstruye_acumulando_respuestas_registradas(self):
        evaluacion_id, actividad_id, estudiante_id = uuid4(), uuid4(), uuid4()
        pregunta_id = uuid4()
        ocurrido_en = datetime.now(UTC)
        evento_inicio = EventoAlmacenado(
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
        respuesta_id = uuid4()
        evento_respuesta = EventoAlmacenado(
            sequence_number=2,
            event_type="RespuestaRegistrada",
            payload={
                "respuesta_id": str(respuesta_id),
                "evaluacion_id": str(evaluacion_id),
                "pregunta_id": str(pregunta_id),
                "numero_intento": 1,
                "contenido": {"opcion_indice": 0},
                "es_correcta": True,
                "ocurrido_en": ocurrido_en.isoformat(),
            },
            occurred_at=ocurrido_en,
        )

        evaluacion = Evaluacion.reconstruir([evento_inicio, evento_respuesta])

        assert len(evaluacion.respuestas) == 1
        respuesta = evaluacion.respuestas[0]
        assert respuesta.id == respuesta_id
        assert respuesta.pregunta_id == pregunta_id
        assert respuesta.numero_intento == 1
        assert respuesta.contenido == {"opcion_indice": 0}
        assert respuesta.es_correcta is True

    def test_reconstruye_aplicando_suspension_y_reanudacion(self):
        evaluacion_id, actividad_id, estudiante_id = uuid4(), uuid4(), uuid4()
        pregunta_id = uuid4()
        ocurrido_en = datetime.now(UTC)
        evento_inicio = EventoAlmacenado(
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
        evento_suspendida = EventoAlmacenado(
            sequence_number=2,
            event_type="EvaluacionSuspendida",
            payload={
                "evaluacion_id": str(evaluacion_id),
                "actor": "estudiante",
                "ocurrido_en": ocurrido_en.isoformat(),
            },
            occurred_at=ocurrido_en,
        )

        evaluacion = Evaluacion.reconstruir([evento_inicio, evento_suspendida])
        assert evaluacion.estado == EstadoEvaluacion.SUSPENDIDA

        evento_reanudada = EventoAlmacenado(
            sequence_number=3,
            event_type="EvaluacionReanudada",
            payload={"evaluacion_id": str(evaluacion_id), "ocurrido_en": ocurrido_en.isoformat()},
            occurred_at=ocurrido_en,
        )

        evaluacion = Evaluacion.reconstruir([evento_inicio, evento_suspendida, evento_reanudada])
        assert evaluacion.estado == EstadoEvaluacion.EN_CURSO


class TestContarRespuestasDe:
    def test_cuenta_solo_las_respuestas_de_la_pregunta_pedida(self):
        pregunta_id, otra_pregunta_id = uuid4(), uuid4()
        evaluacion = Evaluacion.crear(
            uuid4(), uuid4(), [PreguntaAsignada(pregunta_id=pregunta_id, orden=0)]
        )
        evaluacion.respuestas.append(
            Respuesta(
                id=uuid4(),
                pregunta_id=pregunta_id,
                numero_intento=1,
                contenido={},
                es_correcta=False,
            )
        )
        evaluacion.respuestas.append(
            Respuesta(
                id=uuid4(),
                pregunta_id=otra_pregunta_id,
                numero_intento=1,
                contenido={},
                es_correcta=False,
            )
        )

        assert evaluacion.contar_respuestas_de(pregunta_id) == 1
        assert evaluacion.contar_respuestas_de(otra_pregunta_id) == 1
        assert evaluacion.contar_respuestas_de(uuid4()) == 0


class TestValidarParaRegistrarRespuesta:
    def _evaluacion(self, pregunta_id, estado=EstadoEvaluacion.EN_CURSO):
        evaluacion = Evaluacion.crear(
            uuid4(), uuid4(), [PreguntaAsignada(pregunta_id=pregunta_id, orden=0)]
        )
        evaluacion.estado = estado
        return evaluacion

    def test_devuelve_numero_de_intento_uno_para_la_primera_respuesta(self):
        pregunta_id = uuid4()
        evaluacion = self._evaluacion(pregunta_id)

        numero_intento = evaluacion.validar_para_registrar_respuesta(
            pregunta_id, cantidad_intentos_permitidos=2
        )

        assert numero_intento == 1

    def test_devuelve_numero_de_intento_incrementado(self):
        pregunta_id = uuid4()
        evaluacion = self._evaluacion(pregunta_id)
        evaluacion.respuestas.append(
            Respuesta(
                id=uuid4(),
                pregunta_id=pregunta_id,
                numero_intento=1,
                contenido={},
                es_correcta=False,
            )
        )

        numero_intento = evaluacion.validar_para_registrar_respuesta(
            pregunta_id, cantidad_intentos_permitidos=2
        )

        assert numero_intento == 2

    def test_rechaza_pregunta_no_asignada(self):
        evaluacion = self._evaluacion(uuid4())

        with pytest.raises(PreguntaNoAsignada):
            evaluacion.validar_para_registrar_respuesta(uuid4(), cantidad_intentos_permitidos=1)

    def test_rechaza_intentos_agotados(self):
        pregunta_id = uuid4()
        evaluacion = self._evaluacion(pregunta_id)
        evaluacion.respuestas.append(
            Respuesta(
                id=uuid4(),
                pregunta_id=pregunta_id,
                numero_intento=1,
                contenido={},
                es_correcta=False,
            )
        )

        with pytest.raises(IntentosAgotados):
            evaluacion.validar_para_registrar_respuesta(pregunta_id, cantidad_intentos_permitidos=1)

    def test_rechaza_evaluacion_suspendida(self):
        pregunta_id = uuid4()
        evaluacion = self._evaluacion(pregunta_id, estado=EstadoEvaluacion.SUSPENDIDA)

        with pytest.raises(EvaluacionSuspendida):
            evaluacion.validar_para_registrar_respuesta(pregunta_id, cantidad_intentos_permitidos=1)

    def test_rechaza_evaluacion_finalizada(self):
        pregunta_id = uuid4()
        evaluacion = self._evaluacion(pregunta_id, estado=EstadoEvaluacion.FINALIZADA)

        with pytest.raises(EvaluacionYaFinalizada):
            evaluacion.validar_para_registrar_respuesta(pregunta_id, cantidad_intentos_permitidos=1)


def _evaluacion_con_estado(estado):
    evaluacion = Evaluacion.crear(
        uuid4(), uuid4(), [PreguntaAsignada(pregunta_id=uuid4(), orden=0)]
    )
    evaluacion.estado = estado
    return evaluacion


class TestValidarParaSuspender:
    def test_no_levanta_error_sobre_evaluacion_en_curso(self):
        evaluacion = _evaluacion_con_estado(EstadoEvaluacion.EN_CURSO)

        evaluacion.validar_para_suspender()

    def test_rechaza_evaluacion_ya_suspendida(self):
        evaluacion = _evaluacion_con_estado(EstadoEvaluacion.SUSPENDIDA)

        with pytest.raises(EvaluacionYaSuspendida):
            evaluacion.validar_para_suspender()

    def test_rechaza_evaluacion_finalizada(self):
        evaluacion = _evaluacion_con_estado(EstadoEvaluacion.FINALIZADA)

        with pytest.raises(EvaluacionYaFinalizada):
            evaluacion.validar_para_suspender()


class TestValidarParaReanudar:
    def test_no_levanta_error_sobre_evaluacion_suspendida(self):
        evaluacion = _evaluacion_con_estado(EstadoEvaluacion.SUSPENDIDA)

        evaluacion.validar_para_reanudar()

    def test_rechaza_evaluacion_en_curso(self):
        evaluacion = _evaluacion_con_estado(EstadoEvaluacion.EN_CURSO)

        with pytest.raises(EvaluacionNoSuspendida):
            evaluacion.validar_para_reanudar()

    def test_rechaza_evaluacion_finalizada(self):
        evaluacion = _evaluacion_con_estado(EstadoEvaluacion.FINALIZADA)

        with pytest.raises(EvaluacionYaFinalizada):
            evaluacion.validar_para_reanudar()
