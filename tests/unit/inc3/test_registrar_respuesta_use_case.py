from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.errors import (
    EvaluacionNoExiste,
    FueraDePeriodo,
    IntentosAgotados,
    PreguntaNoAsignada,
)
from src.actividad_evaluativa.entities.evaluacion import Evaluacion
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.use_cases.crear_actividad_periodo_abierto import AGGREGATE_TYPE
from src.actividad_evaluativa.use_cases.iniciar_evaluacion import (
    AGGREGATE_TYPE_EVALUACION,
    IniciarEvaluacionUseCase,
)
from src.actividad_evaluativa.use_cases.registrar_respuesta import RegistrarRespuestaUseCase
from tests.unit.inc3._fakes import (
    FakeEstudianteConsultaPort,
    FakeEventStore,
    FakePreguntaConsultaPort,
)


def _evento_actividad_creada(actividad_id, materia_id, apertura, cierre, cantidad_intentos=1):
    return EventoParaAlmacenar(
        event_type="ActividadEvaluativaCreada",
        payload={
            "actividad_id": str(actividad_id),
            "materia_id": str(materia_id),
            "fecha_apertura": apertura.isoformat(),
            "fecha_cierre": cierre.isoformat(),
            "cantidad_preguntas": 1,
            "cantidad_intentos_permitidos": cantidad_intentos,
            "ocurrido_en": apertura.isoformat(),
        },
    )


async def _actividad_vigente(event_store, materia_id, cantidad_intentos=1):
    actividad_id = uuid4()
    apertura = datetime.now(UTC) - timedelta(days=1)
    cierre = apertura + timedelta(days=7)
    await event_store.append(
        AGGREGATE_TYPE,
        actividad_id,
        0,
        [_evento_actividad_creada(actividad_id, materia_id, apertura, cierre, cantidad_intentos)],
    )
    return actividad_id


class TestRegistrarRespuestaUseCase:
    async def test_registra_respuesta_valida(self):
        event_store = FakeEventStore()
        pregunta_id = uuid4()
        materia_id = uuid4()
        actividad_id = await _actividad_vigente(event_store, materia_id)
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.ids_activas[materia_id] = [pregunta_id]
        pregunta_consulta.correcciones[pregunta_id] = True
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_id = uuid4()
        estudiante_consulta.estudiantes.add(estudiante_id)
        iniciar = IniciarEvaluacionUseCase(estudiante_consulta, pregunta_consulta, event_store)
        evaluacion, _ = await iniciar.execute(actividad_id, estudiante_id)
        use_case = RegistrarRespuestaUseCase(pregunta_consulta, event_store)

        respuesta = await use_case.execute(
            evaluacion.id, estudiante_id, pregunta_id, {"opcion_indice": 0}
        )

        assert respuesta.pregunta_id == pregunta_id
        assert respuesta.numero_intento == 1
        assert respuesta.es_correcta is True
        stream = await event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion.id)
        assert len(stream) == 2
        assert stream[1].event_type == "RespuestaRegistrada"

    async def test_segundo_intento_incrementa_numero_intento(self):
        event_store = FakeEventStore()
        pregunta_id = uuid4()
        materia_id = uuid4()
        actividad_id = await _actividad_vigente(event_store, materia_id, cantidad_intentos=2)
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.ids_activas[materia_id] = [pregunta_id]
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_id = uuid4()
        estudiante_consulta.estudiantes.add(estudiante_id)
        iniciar = IniciarEvaluacionUseCase(estudiante_consulta, pregunta_consulta, event_store)
        evaluacion, _ = await iniciar.execute(actividad_id, estudiante_id)
        use_case = RegistrarRespuestaUseCase(pregunta_consulta, event_store)
        await use_case.execute(evaluacion.id, estudiante_id, pregunta_id, {"opcion_indice": 0})

        segunda = await use_case.execute(
            evaluacion.id, estudiante_id, pregunta_id, {"opcion_indice": 1}
        )

        assert segunda.numero_intento == 2
        stream = await event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion.id)
        assert len(stream) == 3

    async def test_rechaza_intentos_agotados(self):
        event_store = FakeEventStore()
        pregunta_id = uuid4()
        materia_id = uuid4()
        actividad_id = await _actividad_vigente(event_store, materia_id, cantidad_intentos=1)
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.ids_activas[materia_id] = [pregunta_id]
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_id = uuid4()
        estudiante_consulta.estudiantes.add(estudiante_id)
        iniciar = IniciarEvaluacionUseCase(estudiante_consulta, pregunta_consulta, event_store)
        evaluacion, _ = await iniciar.execute(actividad_id, estudiante_id)
        use_case = RegistrarRespuestaUseCase(pregunta_consulta, event_store)
        await use_case.execute(evaluacion.id, estudiante_id, pregunta_id, {"opcion_indice": 0})

        with pytest.raises(IntentosAgotados):
            await use_case.execute(evaluacion.id, estudiante_id, pregunta_id, {"opcion_indice": 1})

    async def test_rechaza_pregunta_no_asignada(self):
        event_store = FakeEventStore()
        pregunta_id = uuid4()
        materia_id = uuid4()
        actividad_id = await _actividad_vigente(event_store, materia_id)
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.ids_activas[materia_id] = [pregunta_id]
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_id = uuid4()
        estudiante_consulta.estudiantes.add(estudiante_id)
        iniciar = IniciarEvaluacionUseCase(estudiante_consulta, pregunta_consulta, event_store)
        evaluacion, _ = await iniciar.execute(actividad_id, estudiante_id)
        use_case = RegistrarRespuestaUseCase(pregunta_consulta, event_store)

        with pytest.raises(PreguntaNoAsignada):
            await use_case.execute(evaluacion.id, estudiante_id, uuid4(), {"opcion_indice": 0})

    async def test_rechaza_evaluacion_inexistente(self):
        event_store = FakeEventStore()
        pregunta_consulta = FakePreguntaConsultaPort()
        use_case = RegistrarRespuestaUseCase(pregunta_consulta, event_store)

        with pytest.raises(EvaluacionNoExiste):
            await use_case.execute(uuid4(), uuid4(), uuid4(), {"opcion_indice": 0})

    async def test_rechaza_evaluacion_de_otro_estudiante(self):
        event_store = FakeEventStore()
        pregunta_id = uuid4()
        materia_id = uuid4()
        actividad_id = await _actividad_vigente(event_store, materia_id)
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.ids_activas[materia_id] = [pregunta_id]
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_id = uuid4()
        estudiante_consulta.estudiantes.add(estudiante_id)
        iniciar = IniciarEvaluacionUseCase(estudiante_consulta, pregunta_consulta, event_store)
        evaluacion, _ = await iniciar.execute(actividad_id, estudiante_id)
        use_case = RegistrarRespuestaUseCase(pregunta_consulta, event_store)

        with pytest.raises(EvaluacionNoExiste):
            await use_case.execute(evaluacion.id, uuid4(), pregunta_id, {"opcion_indice": 0})

    async def test_rechaza_fuera_de_periodo(self):
        event_store = FakeEventStore()
        pregunta_id = uuid4()
        materia_id = uuid4()
        actividad_id = uuid4()
        apertura = datetime.now(UTC) - timedelta(days=10)
        cierre = datetime.now(UTC) - timedelta(days=1)
        await event_store.append(
            AGGREGATE_TYPE,
            actividad_id,
            0,
            [_evento_actividad_creada(actividad_id, materia_id, apertura, cierre)],
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.ids_activas[materia_id] = [pregunta_id]
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_id = uuid4()
        estudiante_consulta.estudiantes.add(estudiante_id)
        evaluacion_id = Evaluacion.id_para(actividad_id, estudiante_id)
        preguntas_payload = [{"pregunta_id": str(pregunta_id), "orden": 0}]
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
                        "preguntas_asignadas": preguntas_payload,
                        "ocurrido_en": apertura.isoformat(),
                    },
                )
            ],
        )
        use_case = RegistrarRespuestaUseCase(pregunta_consulta, event_store)

        with pytest.raises(FueraDePeriodo):
            await use_case.execute(evaluacion_id, estudiante_id, pregunta_id, {"opcion_indice": 0})
