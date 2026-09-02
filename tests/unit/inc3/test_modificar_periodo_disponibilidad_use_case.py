from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from src.actividad_evaluativa.entities.errors import (
    ActividadNoExiste,
    NoSePuedeAcortarConEvaluacionesActivas,
    PeriodoInvalido,
)
from src.actividad_evaluativa.entities.evaluacion import EstadoEvaluacion
from src.actividad_evaluativa.entities.ports.evaluacion_activa_query_port import (
    EvaluacionActivaQueryPort,
    EvaluacionActivaResumen,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.use_cases.modificar_periodo_disponibilidad import (
    AGGREGATE_TYPE,
    ModificarPeriodoDisponibilidadUseCase,
)
from tests.unit.inc3._fakes import FakeEventStore


class FakeEvaluacionActivaQueryPort(EvaluacionActivaQueryPort):
    """Devuelve el resumen precargado, sin consultar ningún event store real."""

    def __init__(self, resumen: list[EvaluacionActivaResumen] | None = None) -> None:
        self._resumen = resumen or []

    async def listar_no_finalizadas(self) -> list[EvaluacionActivaResumen]:
        return list(self._resumen)


def _fechas() -> tuple[datetime, datetime]:
    apertura = datetime.now(UTC)
    cierre = apertura + timedelta(days=7)
    return apertura, cierre


async def _crear_actividad(
    event_store: FakeEventStore, fecha_apertura: datetime, fecha_cierre: datetime
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
                    "materia_id": str(uuid4()),
                    "fecha_apertura": fecha_apertura.isoformat(),
                    "fecha_cierre": fecha_cierre.isoformat(),
                    "cantidad_preguntas": 5,
                    "cantidad_intentos_permitidos": 1,
                    "ocurrido_en": fecha_apertura.isoformat(),
                },
            )
        ],
    )
    return actividad_id


def _resumen_activo(actividad_id: UUID) -> EvaluacionActivaResumen:
    return EvaluacionActivaResumen(
        evaluacion_id=uuid4(),
        actividad_id=actividad_id,
        estado=EstadoEvaluacion.EN_CURSO,
        ultima_actividad_en=datetime.now(UTC),
    )


class TestModificarPeriodoDisponibilidadUseCase:
    async def test_extiende_el_plazo_con_evaluaciones_activas(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        evaluacion_activa_query = FakeEvaluacionActivaQueryPort([_resumen_activo(actividad_id)])
        use_case = ModificarPeriodoDisponibilidadUseCase(event_store, evaluacion_activa_query)
        nueva_fecha_cierre = cierre + timedelta(days=3)

        actividad = await use_case.execute(actividad_id, nueva_fecha_cierre)

        assert actividad.fecha_cierre == nueva_fecha_cierre
        stream = await event_store.load(AGGREGATE_TYPE, actividad_id)
        assert len(stream) == 2
        assert stream[1].event_type == "PeriodoDisponibilidadModificado"

    async def test_acorta_el_plazo_sin_evaluaciones_activas(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        evaluacion_activa_query = FakeEvaluacionActivaQueryPort([])
        use_case = ModificarPeriodoDisponibilidadUseCase(event_store, evaluacion_activa_query)
        nueva_fecha_cierre = cierre - timedelta(hours=1)

        actividad = await use_case.execute(actividad_id, nueva_fecha_cierre)

        assert actividad.fecha_cierre == nueva_fecha_cierre

    async def test_rechaza_acortar_con_evaluacion_en_curso(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        evaluacion_activa_query = FakeEvaluacionActivaQueryPort([_resumen_activo(actividad_id)])
        use_case = ModificarPeriodoDisponibilidadUseCase(event_store, evaluacion_activa_query)

        with pytest.raises(NoSePuedeAcortarConEvaluacionesActivas):
            await use_case.execute(actividad_id, cierre - timedelta(hours=1))

        stream = await event_store.load(AGGREGATE_TYPE, actividad_id)
        assert len(stream) == 1

    async def test_ignora_evaluaciones_activas_de_otra_actividad(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        otra_actividad_id = uuid4()
        evaluacion_activa_query = FakeEvaluacionActivaQueryPort(
            [_resumen_activo(otra_actividad_id)]
        )
        use_case = ModificarPeriodoDisponibilidadUseCase(event_store, evaluacion_activa_query)

        actividad = await use_case.execute(actividad_id, cierre - timedelta(hours=1))

        assert actividad.fecha_cierre == cierre - timedelta(hours=1)

    async def test_rechaza_nueva_fecha_anterior_a_apertura(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        use_case = ModificarPeriodoDisponibilidadUseCase(
            event_store, FakeEvaluacionActivaQueryPort()
        )

        with pytest.raises(PeriodoInvalido):
            await use_case.execute(actividad_id, apertura - timedelta(hours=1))

    async def test_rechaza_actividad_inexistente(self):
        event_store = FakeEventStore()
        use_case = ModificarPeriodoDisponibilidadUseCase(
            event_store, FakeEvaluacionActivaQueryPort()
        )

        with pytest.raises(ActividadNoExiste):
            await use_case.execute(uuid4(), datetime.now(UTC))

    async def test_dos_modificaciones_sucesivas_persisten_ambos_eventos(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        use_case = ModificarPeriodoDisponibilidadUseCase(
            event_store, FakeEvaluacionActivaQueryPort()
        )
        primera_extension = cierre + timedelta(days=1)
        segunda_extension = cierre + timedelta(days=2)

        await use_case.execute(actividad_id, primera_extension)
        actividad = await use_case.execute(actividad_id, segunda_extension)

        assert actividad.fecha_cierre == segunda_extension
        stream = await event_store.load(AGGREGATE_TYPE, actividad_id)
        assert len(stream) == 3
