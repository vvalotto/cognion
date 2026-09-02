from uuid import uuid4

from src.actividad_evaluativa.interface_adapters.controllers.actividades_query_controller import (
    ActividadesQueryController,
)
from src.actividad_evaluativa.use_cases.listar_actividades import ListarActividadesUseCase
from src.actividad_evaluativa.use_cases.obtener_actividad import ObtenerActividadUseCase
from tests.unit.inc3.test_listar_actividades_use_case import FakeActividadQueryPort, _resumen


def _controller(query_port: FakeActividadQueryPort) -> ActividadesQueryController:
    return ActividadesQueryController(
        ListarActividadesUseCase(query_port),
        ObtenerActividadUseCase(query_port),
    )


class TestActividadesQueryController:
    async def test_listar_actividades_delega_en_el_use_case(self):
        materia_id = uuid4()
        query_port = FakeActividadQueryPort()
        query_port.resumenes[materia_id] = [_resumen(materia_id)]
        controller = _controller(query_port)

        resultado = await controller.listar_actividades(materia_id)

        assert len(resultado) == 1
        assert resultado[0].materia_id == materia_id

    async def test_obtener_actividad_delega_en_el_use_case(self):
        materia_id = uuid4()
        query_port = FakeActividadQueryPort()
        resumen = _resumen(materia_id)
        query_port.resumenes[materia_id] = [resumen]
        controller = _controller(query_port)

        resultado = await controller.obtener_actividad(resumen.id)

        assert resultado.id == resumen.id
