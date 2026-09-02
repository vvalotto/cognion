from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from src.actividad_evaluativa.entities.evaluacion import EstadoEvaluacion, Evaluacion
from src.actividad_evaluativa.entities.ports.evaluacion_activa_query_port import (
    EvaluacionActivaQueryPort,
    EvaluacionActivaResumen,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.use_cases.finalizar_evaluacion import (
    AGGREGATE_TYPE_EVALUACION,
    FinalizarEvaluacionUseCase,
)
from src.actividad_evaluativa.use_cases.suspender_evaluacion import SuspenderEvaluacionUseCase
from src.actividad_evaluativa.use_cases.verificar_vencimientos import (
    AGGREGATE_TYPE_ACTIVIDAD,
    VerificarVencimientosUseCase,
)
from tests.unit.inc3._fakes import FakeEventStore

UMBRAL_INACTIVIDAD = timedelta(minutes=15)


class FakeEvaluacionActivaQueryPort(EvaluacionActivaQueryPort):
    """Devuelve el resumen precargado, sin consultar ningún event store real."""

    def __init__(self, resumen: list[EvaluacionActivaResumen]) -> None:
        self._resumen = resumen

    async def listar_no_finalizadas(self) -> list[EvaluacionActivaResumen]:
        return list(self._resumen)


async def _crear_actividad(event_store: FakeEventStore, fecha_cierre: datetime) -> UUID:
    actividad_id = uuid4()
    await event_store.append(
        AGGREGATE_TYPE_ACTIVIDAD,
        actividad_id,
        0,
        [
            EventoParaAlmacenar(
                event_type="ActividadEvaluativaCreada",
                payload={
                    "actividad_id": str(actividad_id),
                    "materia_id": str(uuid4()),
                    "fecha_apertura": "2020-01-01T00:00:00+00:00",
                    "fecha_cierre": fecha_cierre.isoformat(),
                    "cantidad_preguntas": 5,
                    "cantidad_intentos_permitidos": 1,
                    "ocurrido_en": "2020-01-01T00:00:00+00:00",
                },
            )
        ],
    )
    return actividad_id


async def _crear_evaluacion_en_curso(event_store: FakeEventStore, actividad_id: UUID) -> UUID:
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
                    "ocurrido_en": "2026-01-01T00:00:00+00:00",
                },
            )
        ],
    )
    return evaluacion_id


def _use_case(
    event_store: FakeEventStore, resumen: list[EvaluacionActivaResumen]
) -> VerificarVencimientosUseCase:
    return VerificarVencimientosUseCase(
        FakeEvaluacionActivaQueryPort(resumen),
        event_store,
        SuspenderEvaluacionUseCase(event_store),
        FinalizarEvaluacionUseCase(event_store),
        UMBRAL_INACTIVIDAD,
    )


class TestVerificarVencimientosUseCase:
    async def test_regla_1_suspende_evaluacion_inactiva(self):
        event_store = FakeEventStore()
        actividad_id = await _crear_actividad(event_store, datetime(2099, 1, 1, tzinfo=UTC))
        evaluacion_id = await _crear_evaluacion_en_curso(event_store, actividad_id)
        ahora = datetime.now(UTC)
        resumen = [
            EvaluacionActivaResumen(
                evaluacion_id=evaluacion_id,
                actividad_id=actividad_id,
                estado=EstadoEvaluacion.EN_CURSO,
                ultima_actividad_en=ahora - timedelta(minutes=30),
            )
        ]
        use_case = _use_case(event_store, resumen)

        resultado = await use_case.execute()

        assert resultado.suspendidas == 1
        assert resultado.finalizadas == 0
        stream = await event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        assert stream[-1].event_type == "EvaluacionSuspendida"
        assert stream[-1].payload["actor"] == "sistema"

    async def test_regla_1_no_afecta_evaluacion_con_actividad_reciente(self):
        event_store = FakeEventStore()
        actividad_id = await _crear_actividad(event_store, datetime(2099, 1, 1, tzinfo=UTC))
        evaluacion_id = await _crear_evaluacion_en_curso(event_store, actividad_id)
        ahora = datetime.now(UTC)
        resumen = [
            EvaluacionActivaResumen(
                evaluacion_id=evaluacion_id,
                actividad_id=actividad_id,
                estado=EstadoEvaluacion.EN_CURSO,
                ultima_actividad_en=ahora - timedelta(minutes=1),
            )
        ]
        use_case = _use_case(event_store, resumen)

        resultado = await use_case.execute()

        assert resultado.suspendidas == 0
        stream = await event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        assert len(stream) == 1

    async def test_regla_2_finaliza_evaluacion_en_curso_de_actividad_vencida(self):
        event_store = FakeEventStore()
        actividad_id = await _crear_actividad(event_store, datetime(2020, 1, 1, tzinfo=UTC))
        evaluacion_id = await _crear_evaluacion_en_curso(event_store, actividad_id)
        resumen = [
            EvaluacionActivaResumen(
                evaluacion_id=evaluacion_id,
                actividad_id=actividad_id,
                estado=EstadoEvaluacion.EN_CURSO,
                ultima_actividad_en=datetime.now(UTC),
            )
        ]
        use_case = _use_case(event_store, resumen)

        resultado = await use_case.execute()

        assert resultado.finalizadas == 1
        stream = await event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        assert stream[-1].event_type == "EvaluacionFinalizada"
        assert stream[-1].payload["actor"] == "sistema"

    async def test_regla_2_finaliza_evaluacion_suspendida_de_actividad_vencida(self):
        event_store = FakeEventStore()
        actividad_id = await _crear_actividad(event_store, datetime(2020, 1, 1, tzinfo=UTC))
        evaluacion_id = await _crear_evaluacion_en_curso(event_store, actividad_id)
        await event_store.append(
            AGGREGATE_TYPE_EVALUACION,
            evaluacion_id,
            1,
            [
                EventoParaAlmacenar(
                    event_type="EvaluacionSuspendida",
                    payload={
                        "evaluacion_id": str(evaluacion_id),
                        "actor": "estudiante",
                        "ocurrido_en": "2026-01-02T00:00:00+00:00",
                    },
                )
            ],
        )
        resumen = [
            EvaluacionActivaResumen(
                evaluacion_id=evaluacion_id,
                actividad_id=actividad_id,
                estado=EstadoEvaluacion.SUSPENDIDA,
                ultima_actividad_en=datetime.now(UTC) - timedelta(hours=1),
            )
        ]
        use_case = _use_case(event_store, resumen)

        resultado = await use_case.execute()

        assert resultado.finalizadas == 1

    async def test_regla_2_no_afecta_evaluacion_de_actividad_vigente(self):
        event_store = FakeEventStore()
        actividad_id = await _crear_actividad(event_store, datetime(2099, 1, 1, tzinfo=UTC))
        evaluacion_id = await _crear_evaluacion_en_curso(event_store, actividad_id)
        resumen = [
            EvaluacionActivaResumen(
                evaluacion_id=evaluacion_id,
                actividad_id=actividad_id,
                estado=EstadoEvaluacion.EN_CURSO,
                ultima_actividad_en=datetime.now(UTC),
            )
        ]
        use_case = _use_case(event_store, resumen)

        resultado = await use_case.execute()

        assert resultado.finalizadas == 0
        stream = await event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        assert len(stream) == 1

    async def test_regla_2_cachea_fecha_cierre_entre_evaluaciones_de_la_misma_actividad(self):
        event_store = FakeEventStore()
        actividad_id = await _crear_actividad(event_store, datetime(2020, 1, 1, tzinfo=UTC))
        evaluacion_id_1 = await _crear_evaluacion_en_curso(event_store, actividad_id)
        evaluacion_id_2 = await _crear_evaluacion_en_curso(event_store, actividad_id)
        ahora = datetime.now(UTC)
        resumen = [
            EvaluacionActivaResumen(
                evaluacion_id=evaluacion_id_1,
                actividad_id=actividad_id,
                estado=EstadoEvaluacion.EN_CURSO,
                ultima_actividad_en=ahora,
            ),
            EvaluacionActivaResumen(
                evaluacion_id=evaluacion_id_2,
                actividad_id=actividad_id,
                estado=EstadoEvaluacion.EN_CURSO,
                ultima_actividad_en=ahora,
            ),
        ]
        use_case = _use_case(event_store, resumen)

        resultado = await use_case.execute()

        assert resultado.finalizadas == 2

    async def test_idempotencia_segunda_corrida_es_no_op(self):
        event_store = FakeEventStore()
        actividad_id = await _crear_actividad(event_store, datetime(2099, 1, 1, tzinfo=UTC))
        evaluacion_id = await _crear_evaluacion_en_curso(event_store, actividad_id)
        ahora = datetime.now(UTC)
        resumen = [
            EvaluacionActivaResumen(
                evaluacion_id=evaluacion_id,
                actividad_id=actividad_id,
                estado=EstadoEvaluacion.EN_CURSO,
                ultima_actividad_en=ahora - timedelta(minutes=30),
            )
        ]
        use_case = _use_case(event_store, resumen)
        primera = await use_case.execute()
        assert primera.suspendidas == 1

        segunda = await use_case.execute()

        assert segunda.suspendidas == 0
        stream = await event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        assert len(stream) == 2
