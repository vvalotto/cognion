from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.errors import ActividadNoExiste
from src.actividad_evaluativa.use_cases.obtener_actividad import ObtenerActividadUseCase
from tests.unit.inc3.test_listar_actividades_use_case import FakeActividadQueryPort, _resumen


class TestObtenerActividadUseCase:
    async def test_devuelve_el_resumen_de_la_actividad_existente(self):
        materia_id = uuid4()
        resumen = _resumen(materia_id)
        query_port = FakeActividadQueryPort()
        query_port.resumenes[materia_id] = [resumen]
        use_case = ObtenerActividadUseCase(query_port)

        resultado = await use_case.execute(resumen.id)

        assert resultado.id == resumen.id
        assert resultado.materia_id == materia_id

    async def test_lanza_actividad_no_existe_si_no_esta(self):
        query_port = FakeActividadQueryPort()
        use_case = ObtenerActividadUseCase(query_port)
        actividad_id = uuid4()

        with pytest.raises(ActividadNoExiste):
            await use_case.execute(actividad_id)
