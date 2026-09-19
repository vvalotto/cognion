"""Tests unitarios de `CrearSesionEnVivoUseCase` y `SesionesEnVivoController` (US-6.1.2)."""

from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import EstadoSesionEnVivo
from src.actividad_evaluativa.entities.errors import (
    ComisionNoExiste,
    PreguntasInsuficientes,
    TiempoLimiteInvalido,
)
from src.actividad_evaluativa.interface_adapters.controllers.sesiones_en_vivo_controller import (
    SesionesEnVivoController,
)
from src.actividad_evaluativa.use_cases.crear_sesion_en_vivo import (
    AGGREGATE_TYPE,
    CrearSesionEnVivoUseCase,
)
from src.actividad_evaluativa.use_cases.iniciar_sesion_en_vivo import (
    IniciarSesionEnVivoUseCase,
)
from src.actividad_evaluativa.use_cases.unirse_a_sesion_en_vivo import (
    UnirseASesionEnVivoUseCase,
)
from tests.unit.inc3._fakes import (
    FakeEstudianteConsultaPort,
    FakeEventStore,
    FakePreguntaConsultaPort,
)
from tests.unit.inc6._fakes import (
    FakeCanalTiempoReal,
    FakeComisionConsultaPort,
    FakeParticipantesSesionQueryPort,
)


def _escenario(cantidad_ids: int = 20):
    comision_id, materia_id = uuid4(), uuid4()
    comision_consulta = FakeComisionConsultaPort()
    comision_consulta.materias[comision_id] = materia_id
    pregunta_consulta = FakePreguntaConsultaPort()
    pregunta_consulta.ids_activas[materia_id] = [uuid4() for _ in range(cantidad_ids)]
    event_store = FakeEventStore()
    use_case = CrearSesionEnVivoUseCase(comision_consulta, pregunta_consulta, event_store)
    return use_case, event_store, pregunta_consulta, comision_id, materia_id


class TestCrearSesionEnVivoUseCase:
    async def test_crea_sesion_y_persiste_primer_evento(self):
        use_case, event_store, pregunta_consulta, comision_id, materia_id = _escenario()

        sesion = await use_case.execute(comision_id, 10, 30)

        assert sesion.comision_id == comision_id
        assert sesion.materia_id == materia_id
        assert sesion.estado == EstadoSesionEnVivo.EN_ESPERA
        assert len(sesion.preguntas) == 10
        ids_del_banco = set(pregunta_consulta.ids_activas[materia_id])
        assert {p.pregunta_id for p in sesion.preguntas} <= ids_del_banco
        assert [p.orden for p in sesion.preguntas] == list(range(10))

        stream = await event_store.load(AGGREGATE_TYPE, sesion.id)
        assert len(stream) == 1
        assert stream[0].sequence_number == 1
        assert stream[0].event_type == "SesionEnVivoCreada"
        assert stream[0].payload["sesion_id"] == str(sesion.id)
        assert stream[0].payload["comision_id"] == str(comision_id)
        assert stream[0].payload["materia_id"] == str(materia_id)
        assert stream[0].payload["tiempo_limite_por_pregunta_segundos"] == 30
        assert len(stream[0].payload["preguntas"]) == 10

    async def test_el_set_fijado_coincide_con_el_persistido(self):
        use_case, event_store, _, comision_id, _ = _escenario()

        sesion = await use_case.execute(comision_id, 5, 30)

        stream = await event_store.load(AGGREGATE_TYPE, sesion.id)
        persistidas = [(p["pregunta_id"], p["orden"]) for p in stream[0].payload["preguntas"]]
        assert persistidas == [(str(p.pregunta_id), p.orden) for p in sesion.preguntas]

    async def test_filtra_por_unidad_y_tema(self):
        use_case, _, pregunta_consulta, comision_id, materia_id = _escenario(cantidad_ids=0)
        ids = [uuid4() for _ in range(6)]
        pregunta_consulta.ids_activas_por_unidad_tema[(materia_id, "U1", "T1")] = ids

        sesion = await use_case.execute(comision_id, 4, 30, "U1", "T1")

        assert {p.pregunta_id for p in sesion.preguntas} <= set(ids)
        assert sesion.unidad_tematica == "U1"
        assert sesion.tema == "T1"

    async def test_comision_inexistente(self):
        use_case, event_store, _, _, _ = _escenario()
        inexistente = uuid4()

        with pytest.raises(ComisionNoExiste):
            await use_case.execute(inexistente, 10, 30)

        assert await event_store.load(AGGREGATE_TYPE, inexistente) == []

    async def test_preguntas_insuficientes_no_persiste_nada(self):
        use_case, event_store, _, comision_id, _ = _escenario(cantidad_ids=5)

        with pytest.raises(PreguntasInsuficientes) as info:
            await use_case.execute(comision_id, 10, 30)

        assert info.value.cantidad_solicitada == 10
        assert info.value.cantidad_disponible == 5
        assert event_store._streams == {}

    async def test_admite_exactamente_las_preguntas_disponibles(self):
        use_case, _, _, comision_id, _ = _escenario(cantidad_ids=5)

        sesion = await use_case.execute(comision_id, 5, 30)

        assert len(sesion.preguntas) == 5

    @pytest.mark.parametrize("tiempo", [0, -1])
    async def test_tiempo_limite_invalido_no_persiste_nada(self, tiempo):
        use_case, event_store, _, comision_id, _ = _escenario()

        with pytest.raises(TiempoLimiteInvalido):
            await use_case.execute(comision_id, 10, tiempo)

        assert event_store._streams == {}


class TestSesionesEnVivoController:
    async def test_crear_delega_en_el_use_case(self):
        use_case, _, _, comision_id, materia_id = _escenario()
        unirse = UnirseASesionEnVivoUseCase(
            FakeEstudianteConsultaPort(),
            FakeEventStore(),
            FakeParticipantesSesionQueryPort(FakeEventStore()),
            FakeCanalTiempoReal(),
        )
        iniciar = IniciarSesionEnVivoUseCase(
            FakeEventStore(), FakePreguntaConsultaPort(), FakeCanalTiempoReal()
        )
        controller = SesionesEnVivoController(use_case, unirse, iniciar)

        sesion = await controller.crear(comision_id, 10, 30)

        assert sesion.comision_id == comision_id
        assert sesion.materia_id == materia_id
        assert len(sesion.preguntas) == 10
