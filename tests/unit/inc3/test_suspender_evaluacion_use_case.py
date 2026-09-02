from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.errors import (
    EvaluacionNoExiste,
    EvaluacionYaSuspendida,
)
from src.actividad_evaluativa.entities.evaluacion import Evaluacion
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.use_cases.suspender_evaluacion import (
    AGGREGATE_TYPE_EVALUACION,
    SuspenderEvaluacionUseCase,
)
from tests.unit.inc3._fakes import FakeEventStore


async def _evaluacion_en_curso(event_store: FakeEventStore) -> tuple[uuid4, uuid4]:
    actividad_id, estudiante_id, pregunta_id = uuid4(), uuid4(), uuid4()
    evaluacion_id = Evaluacion.id_para(actividad_id, estudiante_id)
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
    return evaluacion_id, estudiante_id


class TestSuspenderEvaluacionUseCase:
    async def test_suspende_una_evaluacion_en_curso(self):
        event_store = FakeEventStore()
        evaluacion_id, estudiante_id = await _evaluacion_en_curso(event_store)
        use_case = SuspenderEvaluacionUseCase(event_store)

        evaluacion = await use_case.execute(evaluacion_id, estudiante_id)

        assert evaluacion.estado.value == "Suspendida"
        stream = await event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        assert len(stream) == 2
        assert stream[1].event_type == "EvaluacionSuspendida"
        assert stream[1].payload["actor"] == "estudiante"

    async def test_rechaza_evaluacion_inexistente(self):
        event_store = FakeEventStore()
        use_case = SuspenderEvaluacionUseCase(event_store)

        with pytest.raises(EvaluacionNoExiste):
            await use_case.execute(uuid4(), uuid4())

    async def test_rechaza_evaluacion_de_otro_estudiante(self):
        event_store = FakeEventStore()
        evaluacion_id, _estudiante_id = await _evaluacion_en_curso(event_store)
        use_case = SuspenderEvaluacionUseCase(event_store)

        with pytest.raises(EvaluacionNoExiste):
            await use_case.execute(evaluacion_id, uuid4())

    async def test_rechaza_evaluacion_ya_suspendida(self):
        event_store = FakeEventStore()
        evaluacion_id, estudiante_id = await _evaluacion_en_curso(event_store)
        use_case = SuspenderEvaluacionUseCase(event_store)
        await use_case.execute(evaluacion_id, estudiante_id)

        with pytest.raises(EvaluacionYaSuspendida):
            await use_case.execute(evaluacion_id, estudiante_id)

    async def test_no_valida_periodo_vigente(self):
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
                        "ocurrido_en": "2020-01-01T00:00:00+00:00",
                    },
                )
            ],
        )
        use_case = SuspenderEvaluacionUseCase(event_store)

        evaluacion = await use_case.execute(evaluacion_id, estudiante_id)

        assert evaluacion.estado.value == "Suspendida"

    async def test_actor_sistema_suspende_sin_estudiante_id(self):
        """US-3.2.4: la Policy invoca sin `estudiante_id`, sin chequeo de pertenencia."""
        event_store = FakeEventStore()
        evaluacion_id, _estudiante_id = await _evaluacion_en_curso(event_store)
        use_case = SuspenderEvaluacionUseCase(event_store)

        evaluacion = await use_case.execute(evaluacion_id, actor="sistema")

        assert evaluacion.estado.value == "Suspendida"
        stream = await event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        assert stream[1].payload["actor"] == "sistema"

    async def test_actor_sistema_sobre_ya_suspendida_es_no_op(self):
        """US-3.2.4: idempotencia — no propaga `EvaluacionYaSuspendida`, no reemite el evento."""
        event_store = FakeEventStore()
        evaluacion_id, estudiante_id = await _evaluacion_en_curso(event_store)
        use_case = SuspenderEvaluacionUseCase(event_store)
        await use_case.execute(evaluacion_id, estudiante_id)

        resultado = await use_case.execute(evaluacion_id, actor="sistema")

        assert resultado is None
        stream = await event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        assert len(stream) == 2

    async def test_actor_sistema_sobre_ya_finalizada_es_no_op(self):
        """US-3.2.4: idempotencia — tampoco propaga `EvaluacionYaFinalizada`."""
        event_store = FakeEventStore()
        evaluacion_id, estudiante_id = await _evaluacion_en_curso(event_store)
        await event_store.append(
            AGGREGATE_TYPE_EVALUACION,
            evaluacion_id,
            1,
            [
                EventoParaAlmacenar(
                    event_type="EvaluacionFinalizada",
                    payload={
                        "evaluacion_id": str(evaluacion_id),
                        "actor": "estudiante",
                        "ocurrido_en": "2026-01-03T00:00:00+00:00",
                    },
                )
            ],
        )
        use_case = SuspenderEvaluacionUseCase(event_store)

        resultado = await use_case.execute(evaluacion_id, actor="sistema")

        assert resultado is None
