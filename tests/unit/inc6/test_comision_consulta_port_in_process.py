"""Tests unitarios de `ComisionConsultaPortInProcess` (US-6.1.1).

Reemplaza `_comision_repositorio` por un doble en memoria después de construir el adapter —
evita tocar la base de datos real (mismo criterio que
`tests/unit/inc5/test_comision_consulta_port_in_process.py`).
"""

from unittest.mock import MagicMock
from uuid import uuid4

from src.actividad_evaluativa.frameworks.adapters.comision_consulta_port_in_process import (
    ComisionConsultaPortInProcess,
)
from src.identidad.entities.comision import Comision


class _FakeComisionRepository:
    def __init__(self) -> None:
        self.comisiones: dict = {}

    async def obtener_por_id(self, comision_id):
        return self.comisiones.get(comision_id)


def _construir_adapter() -> tuple[ComisionConsultaPortInProcess, _FakeComisionRepository]:
    adapter = ComisionConsultaPortInProcess(MagicMock())
    fake = _FakeComisionRepository()
    adapter._comision_repositorio = fake  # type: ignore[attr-defined]
    return adapter, fake


class TestObtenerMateriaId:
    async def test_devuelve_el_materia_id_de_la_comision(self):
        adapter, fake = _construir_adapter()
        materia_id = uuid4()
        comision = Comision.crear(materia_id, "lu 10-12", uuid4())
        fake.comisiones[comision.id] = comision

        resultado = await adapter.obtener_materia_id(comision.id)

        assert resultado == materia_id

    async def test_comision_inexistente_devuelve_none(self):
        adapter, _ = _construir_adapter()

        resultado = await adapter.obtener_materia_id(uuid4())

        assert resultado is None
