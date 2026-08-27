from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.errors import (
    EvaluacionNoExiste,
    EvaluacionNoSuspendida,
    FueraDePeriodo,
)
from src.actividad_evaluativa.entities.evaluacion import Evaluacion
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.use_cases.crear_actividad_periodo_abierto import AGGREGATE_TYPE
from src.actividad_evaluativa.use_cases.reanudar_evaluacion import (
    AGGREGATE_TYPE_EVALUACION,
    ReanudarEvaluacionUseCase,
)
from src.actividad_evaluativa.use_cases.suspender_evaluacion import SuspenderEvaluacionUseCase
from tests.unit.inc3._fakes import FakeEventStore


async def _actividad_vigente(event_store, apertura=None, cierre=None):
    actividad_id, materia_id = uuid4(), uuid4()
    apertura = apertura or (datetime.now(UTC) - timedelta(days=1))
    cierre = cierre or (apertura + timedelta(days=7))
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
    return actividad_id


async def _evaluacion_suspendida(event_store, actividad_id):
    estudiante_id, pregunta_id = uuid4(), uuid4()
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
                    "ocurrido_en": datetime.now(UTC).isoformat(),
                },
            )
        ],
    )
    await SuspenderEvaluacionUseCase(event_store).execute(evaluacion_id, estudiante_id)
    return evaluacion_id, estudiante_id


class TestReanudarEvaluacionUseCase:
    async def test_reanuda_una_evaluacion_suspendida(self):
        event_store = FakeEventStore()
        actividad_id = await _actividad_vigente(event_store)
        evaluacion_id, estudiante_id = await _evaluacion_suspendida(event_store, actividad_id)
        use_case = ReanudarEvaluacionUseCase(event_store)

        evaluacion = await use_case.execute(evaluacion_id, estudiante_id)

        assert evaluacion.estado.value == "EnCurso"
        stream = await event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        assert stream[-1].event_type == "EvaluacionReanudada"

    async def test_rechaza_evaluacion_inexistente(self):
        event_store = FakeEventStore()
        use_case = ReanudarEvaluacionUseCase(event_store)

        with pytest.raises(EvaluacionNoExiste):
            await use_case.execute(uuid4(), uuid4())

    async def test_rechaza_evaluacion_de_otro_estudiante(self):
        event_store = FakeEventStore()
        actividad_id = await _actividad_vigente(event_store)
        evaluacion_id, _estudiante_id = await _evaluacion_suspendida(event_store, actividad_id)
        use_case = ReanudarEvaluacionUseCase(event_store)

        with pytest.raises(EvaluacionNoExiste):
            await use_case.execute(evaluacion_id, uuid4())

    async def test_rechaza_evaluacion_no_suspendida(self):
        actividad_id, estudiante_id, pregunta_id = uuid4(), uuid4(), uuid4()
        evaluacion_id = Evaluacion.id_para(actividad_id, estudiante_id)
        event_store = FakeEventStore()
        await _actividad_vigente(event_store)
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
                        "preguntas_asignadas": [
                            {"pregunta_id": str(pregunta_id), "orden": 0}
                        ],
                        "ocurrido_en": datetime.now(UTC).isoformat(),
                    },
                )
            ],
        )
        use_case = ReanudarEvaluacionUseCase(event_store)

        with pytest.raises(EvaluacionNoSuspendida):
            await use_case.execute(evaluacion_id, estudiante_id)

    async def test_rechaza_fuera_de_periodo(self):
        event_store = FakeEventStore()
        apertura = datetime.now(UTC) - timedelta(days=10)
        cierre = datetime.now(UTC) - timedelta(days=1)
        actividad_id = await _actividad_vigente(event_store, apertura=apertura, cierre=cierre)
        evaluacion_id, estudiante_id = await _evaluacion_suspendida(event_store, actividad_id)
        use_case = ReanudarEvaluacionUseCase(event_store)

        with pytest.raises(FueraDePeriodo):
            await use_case.execute(evaluacion_id, estudiante_id)
