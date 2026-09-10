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
    FakeNotificacionPort,
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
    notificacion: FakeNotificacionPort | None = None,
) -> CrearActividadPeriodoAbiertoUseCase:
    return CrearActividadPeriodoAbiertoUseCase(
        materia_consulta, pregunta_consulta, event_store, notificacion or FakeNotificacionPort()
    )


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
        assert stream[0].payload["titulo"] == ""

    async def test_crea_actividad_con_titulo_explicito(self):
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

        actividad, evento = await use_case.execute(
            materia_id, apertura, cierre, 10, 1, titulo="Parcial 1"
        )

        assert actividad.titulo == "Parcial 1"
        assert evento.titulo == "Parcial 1"

    async def test_crea_actividad_restringida_a_comisiones_y_persiste_el_payload(self):
        materia_id = uuid4()
        comision_1, comision_2 = uuid4(), uuid4()
        materia_consulta = FakeMateriaConsultaPort()
        materia_consulta.materias[materia_id] = MateriaDTO(
            id=materia_id, nombre="Ingeniería de Software"
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.conteos[materia_id] = 20
        event_store = FakeEventStore()
        use_case = _use_case(materia_consulta, pregunta_consulta, event_store)
        apertura, cierre = _fechas()

        actividad, evento = await use_case.execute(
            materia_id,
            apertura,
            cierre,
            10,
            1,
            comisiones_ids=frozenset({comision_1, comision_2}),
        )

        assert actividad.comisiones_ids == frozenset({comision_1, comision_2})
        assert evento.comisiones_ids == frozenset({comision_1, comision_2})

        stream = await event_store.load(AGGREGATE_TYPE, actividad.id)
        assert set(stream[0].payload["comisiones_ids"]) == {str(comision_1), str(comision_2)}

    async def test_crea_actividad_sin_comisiones_persiste_lista_vacia(self):
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

        actividad, _evento = await use_case.execute(materia_id, apertura, cierre, 10, 1)

        assert actividad.comisiones_ids == frozenset()
        stream = await event_store.load(AGGREGATE_TYPE, actividad.id)
        assert stream[0].payload["comisiones_ids"] == []

    async def test_crea_actividad_restringida_a_un_tema_y_persiste_el_payload(self):
        materia_id = uuid4()
        materia_consulta = FakeMateriaConsultaPort()
        materia_consulta.materias[materia_id] = MateriaDTO(
            id=materia_id, nombre="Ingeniería de Software"
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.conteos[materia_id] = 20
        pregunta_consulta.conteos_por_tema[(materia_id, "Cohesión")] = 6
        event_store = FakeEventStore()
        use_case = _use_case(materia_consulta, pregunta_consulta, event_store)
        apertura, cierre = _fechas()

        actividad, evento = await use_case.execute(
            materia_id, apertura, cierre, 5, 1, tema="Cohesión"
        )

        assert actividad.tema == "Cohesión"
        assert evento.tema == "Cohesión"
        stream = await event_store.load(AGGREGATE_TYPE, actividad.id)
        assert stream[0].payload["tema"] == "Cohesión"

    async def test_crea_actividad_restringida_a_unidad_y_tema_combinados(self):
        materia_id = uuid4()
        materia_consulta = FakeMateriaConsultaPort()
        materia_consulta.materias[materia_id] = MateriaDTO(
            id=materia_id, nombre="Ingeniería de Software"
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.conteos[materia_id] = 20
        pregunta_consulta.conteos_por_tema[(materia_id, "Cohesión")] = 6
        pregunta_consulta.conteos_por_unidad_tema[
            (materia_id, "Principios de Diseño", "Cohesión")
        ] = 4
        event_store = FakeEventStore()
        use_case = _use_case(materia_consulta, pregunta_consulta, event_store)
        apertura, cierre = _fechas()

        actividad, evento = await use_case.execute(
            materia_id,
            apertura,
            cierre,
            4,
            1,
            unidad_tematica="Principios de Diseño",
            tema="Cohesión",
        )

        assert actividad.unidad_tematica == "Principios de Diseño"
        assert actividad.tema == "Cohesión"
        assert evento.unidad_tematica == "Principios de Diseño"
        stream = await event_store.load(AGGREGATE_TYPE, actividad.id)
        assert stream[0].payload["unidad_tematica"] == "Principios de Diseño"

    async def test_rechaza_preguntas_insuficientes_de_la_combinacion_aunque_el_tema_solo_alcance(
        self,
    ):
        materia_id = uuid4()
        materia_consulta = FakeMateriaConsultaPort()
        materia_consulta.materias[materia_id] = MateriaDTO(
            id=materia_id, nombre="Ingeniería de Software"
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.conteos[materia_id] = 20
        pregunta_consulta.conteos_por_tema[(materia_id, "Cohesión")] = 6
        pregunta_consulta.conteos_por_unidad_tema[
            (materia_id, "Principios de Diseño", "Cohesión")
        ] = 2
        event_store = FakeEventStore()
        use_case = _use_case(materia_consulta, pregunta_consulta, event_store)
        apertura, cierre = _fechas()

        with pytest.raises(PreguntasInsuficientes):
            await use_case.execute(
                materia_id,
                apertura,
                cierre,
                4,
                1,
                unidad_tematica="Principios de Diseño",
                tema="Cohesión",
            )

    async def test_rechaza_preguntas_insuficientes_del_tema_elegido_aunque_el_banco_completo_alcance(
        self,
    ):
        materia_id = uuid4()
        materia_consulta = FakeMateriaConsultaPort()
        materia_consulta.materias[materia_id] = MateriaDTO(
            id=materia_id, nombre="Ingeniería de Software"
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.conteos[materia_id] = 20
        pregunta_consulta.conteos_por_tema[(materia_id, "Cohesión")] = 3
        event_store = FakeEventStore()
        use_case = _use_case(materia_consulta, pregunta_consulta, event_store)
        apertura, cierre = _fechas()

        with pytest.raises(PreguntasInsuficientes):
            await use_case.execute(materia_id, apertura, cierre, 5, 1, tema="Cohesión")

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

    async def test_dispara_notificar_apertura_con_los_datos_de_la_actividad_creada(self):
        materia_id = uuid4()
        comision_1 = uuid4()
        materia_consulta = FakeMateriaConsultaPort()
        materia_consulta.materias[materia_id] = MateriaDTO(
            id=materia_id, nombre="Ingeniería de Software"
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.conteos[materia_id] = 20
        event_store = FakeEventStore()
        notificacion = FakeNotificacionPort()
        use_case = _use_case(materia_consulta, pregunta_consulta, event_store, notificacion)
        apertura, cierre = _fechas()

        actividad, _evento = await use_case.execute(
            materia_id,
            apertura,
            cierre,
            10,
            1,
            titulo="Parcial 1",
            comisiones_ids=frozenset({comision_1}),
        )

        assert len(notificacion.aperturas) == 1
        llamada = notificacion.aperturas[0]
        assert llamada["actividad_id"] == actividad.id
        assert llamada["materia_id"] == materia_id
        assert llamada["materia_nombre"] == "Ingeniería de Software"
        assert llamada["titulo"] == "Parcial 1"
        assert llamada["fecha_apertura"] == apertura
        assert llamada["fecha_cierre"] == cierre
        assert llamada["comisiones_ids"] == [comision_1]

    async def test_rechaza_materia_inexistente(self):
        materia_consulta = FakeMateriaConsultaPort()
        pregunta_consulta = FakePreguntaConsultaPort()
        event_store = FakeEventStore()
        use_case = _use_case(materia_consulta, pregunta_consulta, event_store)
        apertura, cierre = _fechas()

        with pytest.raises(MateriaNoExiste):
            await use_case.execute(uuid4(), apertura, cierre, 10, 1)
