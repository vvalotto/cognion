from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.actividad_evaluativa.entities.eventos import ActividadEvaluativaCreada
from src.actividad_evaluativa.entities.ports.materia_consulta_port import MateriaDTO
from src.actividad_evaluativa.interface_adapters.controllers.actividades_controller import (
    ActividadesController,
)
from src.actividad_evaluativa.use_cases.cerrar_actividad import CerrarActividadUseCase
from src.actividad_evaluativa.use_cases.crear_actividad_periodo_abierto import (
    CrearActividadPeriodoAbiertoUseCase,
)
from src.actividad_evaluativa.use_cases.finalizar_evaluacion import FinalizarEvaluacionUseCase
from src.actividad_evaluativa.use_cases.modificar_periodo_disponibilidad import (
    ModificarPeriodoDisponibilidadUseCase,
)
from src.actividad_evaluativa.use_cases.modificar_titulo_actividad import (
    ModificarTituloActividadUseCase,
)
from tests.unit.inc3._fakes import (
    FakeEventStore,
    FakeMateriaConsultaPort,
    FakePreguntaConsultaPort,
)
from tests.unit.inc3.test_modificar_periodo_disponibilidad_use_case import (
    FakeEvaluacionActivaQueryPort,
    _crear_actividad,
)


def _controller(event_store: FakeEventStore | None = None) -> ActividadesController:
    event_store = event_store or FakeEventStore()
    materia_consulta = FakeMateriaConsultaPort()
    pregunta_consulta = FakePreguntaConsultaPort()
    return ActividadesController(
        CrearActividadPeriodoAbiertoUseCase(materia_consulta, pregunta_consulta, event_store),
        ModificarPeriodoDisponibilidadUseCase(event_store, FakeEvaluacionActivaQueryPort()),
        CerrarActividadUseCase(
            event_store, FakeEvaluacionActivaQueryPort(), FinalizarEvaluacionUseCase(event_store)
        ),
        ModificarTituloActividadUseCase(event_store),
    )


class TestActividadesController:
    async def test_crear_actividad_delega_al_use_case(self):
        materia_id = uuid4()
        materia_consulta = FakeMateriaConsultaPort()
        materia_consulta.materias[materia_id] = MateriaDTO(id=materia_id, nombre="Materia")
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.conteos[materia_id] = 20
        event_store = FakeEventStore()
        controller = ActividadesController(
            CrearActividadPeriodoAbiertoUseCase(materia_consulta, pregunta_consulta, event_store),
            ModificarPeriodoDisponibilidadUseCase(event_store, FakeEvaluacionActivaQueryPort()),
            CerrarActividadUseCase(
                event_store,
                FakeEvaluacionActivaQueryPort(),
                FinalizarEvaluacionUseCase(event_store),
            ),
            ModificarTituloActividadUseCase(event_store),
        )
        apertura = datetime.now(UTC)
        cierre = apertura + timedelta(days=7)

        actividad, evento = await controller.crear_actividad(materia_id, apertura, cierre, 10, 1)

        assert actividad.materia_id == materia_id
        assert actividad.cantidad_preguntas == 10
        assert isinstance(evento, ActividadEvaluativaCreada)
        assert evento.actividad_id == actividad.id

    async def test_modificar_periodo_disponibilidad_delega_al_use_case(self):
        event_store = FakeEventStore()
        apertura = datetime.now(UTC)
        cierre = apertura + timedelta(days=7)
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        controller = _controller(event_store)
        nueva_fecha_cierre = cierre + timedelta(days=3)

        actividad = await controller.modificar_periodo_disponibilidad(
            actividad_id, nueva_fecha_cierre
        )

        assert actividad.fecha_cierre == nueva_fecha_cierre

    async def test_cerrar_actividad_delega_al_use_case(self):
        event_store = FakeEventStore()
        apertura = datetime.now(UTC)
        cierre = apertura + timedelta(days=7)
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        controller = _controller(event_store)

        actividad = await controller.cerrar_actividad(actividad_id)

        assert actividad.cerrada_manualmente is True

    async def test_modificar_titulo_delega_al_use_case(self):
        event_store = FakeEventStore()
        apertura = datetime.now(UTC)
        cierre = apertura + timedelta(days=7)
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        controller = _controller(event_store)

        actividad = await controller.modificar_titulo(actividad_id, "Parcial 1 (final)")

        assert actividad.titulo == "Parcial 1 (final)"
