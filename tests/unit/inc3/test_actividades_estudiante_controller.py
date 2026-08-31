from datetime import UTC, datetime
from uuid import uuid4

from src.actividad_evaluativa.interface_adapters.controllers.actividades_estudiante_controller import (
    ActividadesEstudianteController,
)
from src.actividad_evaluativa.use_cases.listar_actividades_visibles import (
    ListarActividadesVisiblesUseCase,
)
from tests.unit.inc3.test_listar_actividades_visibles_use_case import (
    FakeActividadQueryPort,
    FakeEvaluacionEstudianteQueryPort,
    _resumen,
)


class TestActividadesEstudianteController:
    async def test_listar_actividades_visibles_delega_en_el_use_case(self):
        materia_id = uuid4()
        estudiante_id = uuid4()
        ahora = datetime.now(UTC)
        actividad_query = FakeActividadQueryPort()
        actividad_query.resumenes[materia_id] = [_resumen(materia_id, ahora)]
        evaluacion_query = FakeEvaluacionEstudianteQueryPort()
        controller = ActividadesEstudianteController(
            ListarActividadesVisiblesUseCase(actividad_query, evaluacion_query)
        )

        resultado = await controller.listar_actividades_visibles(materia_id, estudiante_id)

        assert len(resultado) == 1
        assert resultado[0].materia_id == materia_id
