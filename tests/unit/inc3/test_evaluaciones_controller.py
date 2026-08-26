from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.interface_adapters.controllers.evaluaciones_controller import (
    EvaluacionesController,
)
from src.actividad_evaluativa.use_cases.crear_actividad_periodo_abierto import AGGREGATE_TYPE
from src.actividad_evaluativa.use_cases.iniciar_evaluacion import IniciarEvaluacionUseCase
from tests.unit.inc3._fakes import (
    FakeEstudianteConsultaPort,
    FakeEventStore,
    FakePreguntaConsultaPort,
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
        controller = EvaluacionesController(
            IniciarEvaluacionUseCase(estudiante_consulta, pregunta_consulta, event_store)
        )

        evaluacion, creada = await controller.iniciar_evaluacion(actividad_id, estudiante_id)

        assert creada is True
        assert evaluacion.actividad_id == actividad_id
        assert evaluacion.estudiante_id == estudiante_id
        assert len(evaluacion.preguntas_asignadas) == 2
