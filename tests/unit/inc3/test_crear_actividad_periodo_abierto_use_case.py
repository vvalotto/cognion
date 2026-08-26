from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.errors import (
    CantidadIntentosInvalida,
    MateriaNoExiste,
    PeriodoInvalido,
    PreguntasInsuficientes,
)
from src.actividad_evaluativa.entities.eventos import ActividadEvaluativaCreada
from src.actividad_evaluativa.entities.ports.materia_consulta_port import MateriaDTO
from src.actividad_evaluativa.use_cases.crear_actividad_periodo_abierto import (
    AGGREGATE_TYPE,
    CrearActividadPeriodoAbiertoUseCase,
)
from tests.unit.inc3._fakes import (
    FakeEventStore,
    FakeMateriaConsultaPort,
    FakePreguntaConsultaPort,
)


def _fechas() -> tuple[datetime, datetime]:
    apertura = datetime.now(UTC)
    cierre = apertura + timedelta(days=7)
    return apertura, cierre


def _use_case(
    materia_consulta: FakeMateriaConsultaPort,
    pregunta_consulta: FakePreguntaConsultaPort,
    event_store: FakeEventStore,
) -> CrearActividadPeriodoAbiertoUseCase:
    return CrearActividadPeriodoAbiertoUseCase(materia_consulta, pregunta_consulta, event_store)


class TestCrearActividadPeriodoAbiertoUseCase:
    async def test_crea_actividad_y_persiste_evento(self):
        materia_id = uuid4()
        materia_consulta = FakeMateriaConsultaPort()
        materia_consulta.materias[materia_id] = MateriaDTO(
            id=materia_id, nombre="Ingeniería de Software"
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.conteos[materia_id] = 20
        event_store = FakeEventStore()
        use_case = _use_case(materia_consulta, pregunta_consulta, event_store)
        apertura, cierre = _fechas()

        actividad, evento = await use_case.execute(materia_id, apertura, cierre, 10, 1)

        assert actividad.materia_id == materia_id
        assert actividad.cerrada_manualmente is False
        assert isinstance(evento, ActividadEvaluativaCreada)
        assert evento.actividad_id == actividad.id

        stream = await event_store.load(AGGREGATE_TYPE, actividad.id)
        assert len(stream) == 1
        assert stream[0].event_type == "ActividadEvaluativaCreada"
        assert stream[0].payload["materia_id"] == str(materia_id)
        assert stream[0].payload["cantidad_preguntas"] == 10

    async def test_rechaza_preguntas_insuficientes(self):
        materia_id = uuid4()
        materia_consulta = FakeMateriaConsultaPort()
        materia_consulta.materias[materia_id] = MateriaDTO(id=materia_id, nombre="Materia")
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.conteos[materia_id] = 5
        event_store = FakeEventStore()
        use_case = _use_case(materia_consulta, pregunta_consulta, event_store)
        apertura, cierre = _fechas()

        with pytest.raises(PreguntasInsuficientes):
            await use_case.execute(materia_id, apertura, cierre, 10, 1)

        assert await event_store.load(AGGREGATE_TYPE, materia_id) == []

    async def test_rechaza_periodo_invalido(self):
        materia_id = uuid4()
        materia_consulta = FakeMateriaConsultaPort()
        materia_consulta.materias[materia_id] = MateriaDTO(id=materia_id, nombre="Materia")
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.conteos[materia_id] = 20
        event_store = FakeEventStore()
        use_case = _use_case(materia_consulta, pregunta_consulta, event_store)
        apertura, cierre = _fechas()

        with pytest.raises(PeriodoInvalido):
            await use_case.execute(materia_id, cierre, apertura, 10, 1)

    async def test_rechaza_cantidad_intentos_invalida(self):
        materia_id = uuid4()
        materia_consulta = FakeMateriaConsultaPort()
        materia_consulta.materias[materia_id] = MateriaDTO(id=materia_id, nombre="Materia")
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.conteos[materia_id] = 20
        event_store = FakeEventStore()
        use_case = _use_case(materia_consulta, pregunta_consulta, event_store)
        apertura, cierre = _fechas()

        with pytest.raises(CantidadIntentosInvalida):
            await use_case.execute(materia_id, apertura, cierre, 10, 0)

    async def test_rechaza_materia_inexistente(self):
        materia_consulta = FakeMateriaConsultaPort()
        pregunta_consulta = FakePreguntaConsultaPort()
        event_store = FakeEventStore()
        use_case = _use_case(materia_consulta, pregunta_consulta, event_store)
        apertura, cierre = _fechas()

        with pytest.raises(MateriaNoExiste):
            await use_case.execute(uuid4(), apertura, cierre, 10, 1)
