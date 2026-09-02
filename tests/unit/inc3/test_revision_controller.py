from uuid import uuid4

from src.actividad_evaluativa.entities.evaluacion import Evaluacion
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.interface_adapters.controllers.revision_controller import (
    RevisionController,
)
from src.actividad_evaluativa.use_cases.obtener_revision_evaluacion import (
    AGGREGATE_TYPE_EVALUACION,
    ObtenerRevisionEvaluacionUseCase,
)
from tests.unit.inc3._fakes import FakeEventStore, FakePreguntaConsultaPort


class TestRevisionController:
    async def test_obtener_revision_delega_al_use_case(self):
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
                    event_type="EvaluacionFinalizada",
                    payload={
                        "evaluacion_id": str(evaluacion_id),
                        "actor": "estudiante",
                        "ocurrido_en": "2026-01-01T01:00:00+00:00",
                    },
                ),
            ],
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        controller = RevisionController(
            ObtenerRevisionEvaluacionUseCase(pregunta_consulta, event_store)
        )

        revision = await controller.obtener_revision(evaluacion_id, estudiante_id)

        assert revision.evaluacion_id == evaluacion_id
        assert revision.cantidad_preguntas == 1
