from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.actividad_evaluativa.entities.eventos import ActividadEvaluativaCreada
from src.actividad_evaluativa.entities.ports.materia_consulta_port import MateriaDTO
from src.actividad_evaluativa.interface_adapters.controllers.actividades_controller import (
    ActividadesController,
)
from src.actividad_evaluativa.use_cases.crear_actividad_periodo_abierto import (
    CrearActividadPeriodoAbiertoUseCase,
)
from tests.unit.inc3._fakes import (
    FakeEventStore,
    FakeMateriaConsultaPort,
    FakePreguntaConsultaPort,
)


class TestActividadesController:
    async def test_crear_actividad_delega_al_use_case(self):
        materia_id = uuid4()
        materia_consulta = FakeMateriaConsultaPort()
        materia_consulta.materias[materia_id] = MateriaDTO(id=materia_id, nombre="Materia")
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.conteos[materia_id] = 20
        controller = ActividadesController(
            CrearActividadPeriodoAbiertoUseCase(
                materia_consulta, pregunta_consulta, FakeEventStore()
            )
        )
        apertura = datetime.now(UTC)
        cierre = apertura + timedelta(days=7)

        actividad, evento = await controller.crear_actividad(materia_id, apertura, cierre, 10, 1)

        assert actividad.materia_id == materia_id
        assert actividad.cantidad_preguntas == 10
        assert isinstance(evento, ActividadEvaluativaCreada)
        assert evento.actividad_id == actividad.id
