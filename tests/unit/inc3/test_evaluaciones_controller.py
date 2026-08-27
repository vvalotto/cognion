from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.actividad_evaluativa.entities.evaluacion import EstadoEvaluacion
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.interface_adapters.controllers.evaluaciones_controller import (
    EvaluacionesController,
)
from src.actividad_evaluativa.use_cases.crear_actividad_periodo_abierto import AGGREGATE_TYPE
from src.actividad_evaluativa.use_cases.iniciar_evaluacion import IniciarEvaluacionUseCase
from src.actividad_evaluativa.use_cases.reanudar_evaluacion import ReanudarEvaluacionUseCase
from src.actividad_evaluativa.use_cases.registrar_respuesta import RegistrarRespuestaUseCase
from src.actividad_evaluativa.use_cases.suspender_evaluacion import SuspenderEvaluacionUseCase
from tests.unit.inc3._fakes import (
    FakeEstudianteConsultaPort,
    FakeEventStore,
    FakePreguntaConsultaPort,
)


def _controller(estudiante_consulta, pregunta_consulta, event_store):
    return EvaluacionesController(
        IniciarEvaluacionUseCase(estudiante_consulta, pregunta_consulta, event_store),
        RegistrarRespuestaUseCase(pregunta_consulta, event_store),
        SuspenderEvaluacionUseCase(event_store),
        ReanudarEvaluacionUseCase(event_store),
    )


class TestEvaluacionesController:
    async def test_iniciar_evaluacion_delega_al_use_case(self):
        materia_id, estudiante_id = uuid4(), uuid4()
        actividad_id = uuid4()
        apertura = datetime.now(UTC) - timedelta(days=1)
        cierre = apertura + timedelta(days=7)
        event_store = FakeEventStore()
        await event_store.append(
            AGGREGATE_TYPE,
            actividad_id,
            0,
            [
                EventoParaAlmacenar(
                    event_type="ActividadEvaluativaCreada",
                    payload={
                        "actividad_id": str(actividad_id),
                        "materia_id": str(materia_id),
                        "fecha_apertura": apertura.isoformat(),
                        "fecha_cierre": cierre.isoformat(),
                        "cantidad_preguntas": 2,
                        "cantidad_intentos_permitidos": 1,
                        "ocurrido_en": apertura.isoformat(),
                    },
                )
            ],
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.ids_activas[materia_id] = [uuid4(), uuid4(), uuid4()]
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_consulta.estudiantes.add(estudiante_id)
        controller = _controller(estudiante_consulta, pregunta_consulta, event_store)

        evaluacion, creada = await controller.iniciar_evaluacion(actividad_id, estudiante_id)

        assert creada is True
        assert evaluacion.actividad_id == actividad_id
        assert evaluacion.estudiante_id == estudiante_id
        assert len(evaluacion.preguntas_asignadas) == 2


class TestEvaluacionesControllerRegistrarRespuesta:
    async def test_registrar_respuesta_delega_al_use_case(self):
        materia_id, estudiante_id = uuid4(), uuid4()
        actividad_id = uuid4()
        pregunta_id = uuid4()
        apertura = datetime.now(UTC) - timedelta(days=1)
        cierre = apertura + timedelta(days=7)
        event_store = FakeEventStore()
        await event_store.append(
            AGGREGATE_TYPE,
            actividad_id,
            0,
            [
                EventoParaAlmacenar(
                    event_type="ActividadEvaluativaCreada",
                    payload={
                        "actividad_id": str(actividad_id),
                        "materia_id": str(materia_id),
                        "fecha_apertura": apertura.isoformat(),
                        "fecha_cierre": cierre.isoformat(),
                        "cantidad_preguntas": 1,
                        "cantidad_intentos_permitidos": 1,
                        "ocurrido_en": apertura.isoformat(),
                    },
                )
            ],
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.ids_activas[materia_id] = [pregunta_id]
        pregunta_consulta.correcciones[pregunta_id] = True
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_consulta.estudiantes.add(estudiante_id)
        controller = _controller(estudiante_consulta, pregunta_consulta, event_store)
        evaluacion, _creada = await controller.iniciar_evaluacion(actividad_id, estudiante_id)

        respuesta = await controller.registrar_respuesta(
            evaluacion.id, estudiante_id, pregunta_id, {"opcion_indice": 0}
        )

        assert respuesta.pregunta_id == pregunta_id
        assert respuesta.numero_intento == 1


class TestEvaluacionesControllerSuspenderReanudar:
    async def _iniciar(self):
        materia_id, estudiante_id = uuid4(), uuid4()
        actividad_id = uuid4()
        apertura = datetime.now(UTC) - timedelta(days=1)
        cierre = apertura + timedelta(days=7)
        event_store = FakeEventStore()
        await event_store.append(
            AGGREGATE_TYPE,
            actividad_id,
            0,
            [
                EventoParaAlmacenar(
                    event_type="ActividadEvaluativaCreada",
                    payload={
                        "actividad_id": str(actividad_id),
                        "materia_id": str(materia_id),
                        "fecha_apertura": apertura.isoformat(),
                        "fecha_cierre": cierre.isoformat(),
                        "cantidad_preguntas": 1,
                        "cantidad_intentos_permitidos": 1,
                        "ocurrido_en": apertura.isoformat(),
                    },
                )
            ],
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.ids_activas[materia_id] = [uuid4()]
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_consulta.estudiantes.add(estudiante_id)
        controller = _controller(estudiante_consulta, pregunta_consulta, event_store)
        evaluacion, _creada = await controller.iniciar_evaluacion(actividad_id, estudiante_id)
        return controller, evaluacion, estudiante_id

    async def test_suspender_delega_al_use_case(self):
        controller, evaluacion, estudiante_id = await self._iniciar()

        suspendida = await controller.suspender_evaluacion(evaluacion.id, estudiante_id)

        assert suspendida.estado == EstadoEvaluacion.SUSPENDIDA

    async def test_reanudar_delega_al_use_case(self):
        controller, evaluacion, estudiante_id = await self._iniciar()
        await controller.suspender_evaluacion(evaluacion.id, estudiante_id)

        reanudada = await controller.reanudar_evaluacion(evaluacion.id, estudiante_id)

        assert reanudada.estado == EstadoEvaluacion.EN_CURSO
