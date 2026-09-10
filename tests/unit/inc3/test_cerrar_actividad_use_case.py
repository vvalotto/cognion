from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from src.actividad_evaluativa.entities.errors import ActividadNoExiste, ActividadYaCerrada
from src.actividad_evaluativa.entities.evaluacion import EstadoEvaluacion, Evaluacion
from src.actividad_evaluativa.entities.ports.evaluacion_activa_query_port import (
    EvaluacionActivaResumen,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.entities.ports.materia_consulta_port import MateriaDTO
from src.actividad_evaluativa.use_cases.cerrar_actividad import (
    AGGREGATE_TYPE,
    CerrarActividadUseCase,
)
from src.actividad_evaluativa.use_cases.finalizar_evaluacion import (
    AGGREGATE_TYPE_EVALUACION,
    FinalizarEvaluacionUseCase,
)
from tests.unit.inc3._fakes import FakeEventStore, FakeMateriaConsultaPort, FakeNotificacionPort
from tests.unit.inc3.test_modificar_periodo_disponibilidad_use_case import (
    FakeEvaluacionActivaQueryPort,
    _resumen_activo,
)


def _use_case(
    event_store: FakeEventStore,
    evaluacion_activa_query,
    materia_consulta: FakeMateriaConsultaPort | None = None,
    notificacion: FakeNotificacionPort | None = None,
) -> CerrarActividadUseCase:
    return CerrarActividadUseCase(
        event_store,
        evaluacion_activa_query,
        FinalizarEvaluacionUseCase(event_store),
        materia_consulta or FakeMateriaConsultaPort(),
        notificacion or FakeNotificacionPort(),
    )


def _fechas() -> tuple[datetime, datetime]:
    apertura = datetime.now(UTC)
    cierre = apertura + timedelta(days=7)
    return apertura, cierre


async def _crear_actividad(
    event_store: FakeEventStore,
    fecha_apertura: datetime,
    fecha_cierre: datetime,
    materia_id: UUID | None = None,
    titulo: str = "",
    comisiones_ids: list[UUID] | None = None,
) -> UUID:
    actividad_id = uuid4()
    await event_store.append(
        AGGREGATE_TYPE,
        actividad_id,
        0,
        [
            EventoParaAlmacenar(
                event_type="ActividadEvaluativaCreada",
                payload={
                    "actividad_id": str(actividad_id),
                    "materia_id": str(materia_id or uuid4()),
                    "fecha_apertura": fecha_apertura.isoformat(),
                    "fecha_cierre": fecha_cierre.isoformat(),
                    "cantidad_preguntas": 5,
                    "cantidad_intentos_permitidos": 1,
                    "titulo": titulo,
                    "comisiones_ids": [str(c) for c in (comisiones_ids or [])],
                    "ocurrido_en": fecha_apertura.isoformat(),
                },
            )
        ],
    )
    return actividad_id


async def _iniciar_evaluacion(event_store: FakeEventStore, actividad_id: UUID) -> UUID:
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


class TestCerrarActividadUseCase:
    async def test_cierra_actividad_sin_evaluaciones_activas(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        use_case = _use_case(event_store, FakeEvaluacionActivaQueryPort())

        actividad = await use_case.execute(actividad_id)

        assert actividad.cerrada_manualmente is True
        stream = await event_store.load(AGGREGATE_TYPE, actividad_id)
        assert len(stream) == 2
        assert stream[1].event_type == "ActividadEvaluativaCerrada"

    async def test_cierra_actividad_finaliza_en_cascada_evaluacion_en_curso(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        evaluacion_id = await _iniciar_evaluacion(event_store, actividad_id)
        resumen = EvaluacionActivaResumen(
            evaluacion_id=evaluacion_id,
            actividad_id=actividad_id,
            estado=EstadoEvaluacion.EN_CURSO,
            ultima_actividad_en=datetime.now(UTC),
        )
        evaluacion_activa_query = FakeEvaluacionActivaQueryPort([resumen])
        use_case = _use_case(event_store, evaluacion_activa_query)

        await use_case.execute(actividad_id)

        stream_evaluacion = await event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion_id)
        assert stream_evaluacion[-1].event_type == "EvaluacionFinalizada"
        assert stream_evaluacion[-1].payload["actor"] == "sistema"

    async def test_ignora_evaluaciones_activas_de_otra_actividad(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        otra_actividad_id = uuid4()
        evaluacion_activa_query = FakeEvaluacionActivaQueryPort(
            [_resumen_activo(otra_actividad_id)]
        )
        use_case = _use_case(event_store, evaluacion_activa_query)

        actividad = await use_case.execute(actividad_id)

        assert actividad.cerrada_manualmente is True

    async def test_rechaza_actividad_ya_cerrada(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        use_case = _use_case(event_store, FakeEvaluacionActivaQueryPort())
        await use_case.execute(actividad_id)

        with pytest.raises(ActividadYaCerrada):
            await use_case.execute(actividad_id)

        stream = await event_store.load(AGGREGATE_TYPE, actividad_id)
        assert len(stream) == 2

    async def test_rechaza_actividad_inexistente(self):
        event_store = FakeEventStore()
        use_case = _use_case(event_store, FakeEvaluacionActivaQueryPort())

        with pytest.raises(ActividadNoExiste):
            await use_case.execute(uuid4())

    async def test_dispara_notificacion_de_cierre_con_materia_y_titulo(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        materia_id = uuid4()
        comision_a = uuid4()
        actividad_id = await _crear_actividad(
            event_store,
            apertura,
            cierre,
            materia_id=materia_id,
            titulo="Parcial 1",
            comisiones_ids=[comision_a],
        )
        materia_consulta = FakeMateriaConsultaPort()
        materia_consulta.materias[materia_id] = MateriaDTO(id=materia_id, nombre="Materia X")
        notificacion = FakeNotificacionPort()
        use_case = _use_case(
            event_store,
            FakeEvaluacionActivaQueryPort(),
            materia_consulta=materia_consulta,
            notificacion=notificacion,
        )

        await use_case.execute(actividad_id)

        assert len(notificacion.cierres) == 1
        cierre_notificado = notificacion.cierres[0]
        assert cierre_notificado["actividad_id"] == actividad_id
        assert cierre_notificado["materia_id"] == materia_id
        assert cierre_notificado["materia_nombre"] == "Materia X"
        assert cierre_notificado["titulo"] == "Parcial 1"
        assert cierre_notificado["comisiones_ids"] == [comision_a]

    async def test_no_dispara_notificacion_si_ya_estaba_cerrada(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        notificacion = FakeNotificacionPort()
        use_case = _use_case(event_store, FakeEvaluacionActivaQueryPort(), notificacion=notificacion)
        await use_case.execute(actividad_id)

        with pytest.raises(ActividadYaCerrada):
            await use_case.execute(actividad_id)

        assert len(notificacion.cierres) == 1
