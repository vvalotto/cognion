"""Tests unitarios de la lógica de `ComisionConsultaPortInProcess` (US-5.1.1).

Reemplaza `_comision_query` por un doble en memoria después de construir el adapter — evita
tocar la base de datos real (`SQLAlchemyComisionQueryRepository` solo se toca en
`tests/integration/inc5/`, mismo criterio que el resto del proyecto para adapters in-process
que envuelven un gateway SQLAlchemy).
"""

from unittest.mock import MagicMock
from uuid import uuid4

from src.identidad.entities.comision import Comision
from src.identidad.entities.ports.comision_query_port import EstudianteConEmail
from src.notificaciones.frameworks.adapters.comision_consulta_port_in_process import (
    ComisionConsultaPortInProcess,
)


class _FakeComisionQuery:
    def __init__(self) -> None:
        self.comisiones_por_materia: dict = {}
        self.estudiantes_con_email_por_comision: dict = {}

    async def listar_comisiones_por_materia(self, materia_id, incluir_inactivas=False):
        return self.comisiones_por_materia.get(materia_id, [])

    async def listar_estudiantes_con_email(self, comision_id):
        return self.estudiantes_con_email_por_comision.get(comision_id, [])


def _construir_adapter() -> tuple[ComisionConsultaPortInProcess, _FakeComisionQuery]:
    adapter = ComisionConsultaPortInProcess(MagicMock())
    fake = _FakeComisionQuery()
    adapter._comision_query = fake  # type: ignore[attr-defined]
    return adapter, fake


class TestListarComisionesPorMateria:
    async def test_devuelve_solo_los_ids(self):
        adapter, fake = _construir_adapter()
        materia_id = uuid4()
        comision_1 = Comision.crear(materia_id, "lu 10-12", uuid4())
        comision_2 = Comision.crear(materia_id, "ma 14-16", uuid4())
        fake.comisiones_por_materia[materia_id] = [comision_1, comision_2]

        resultado = await adapter.listar_comisiones_por_materia(materia_id)

        assert set(resultado) == {comision_1.id, comision_2.id}

    async def test_materia_sin_comisiones_devuelve_lista_vacia(self):
        adapter, _ = _construir_adapter()

        resultado = await adapter.listar_comisiones_por_materia(uuid4())

        assert resultado == []


class TestListarDestinatarios:
    async def test_roster_combinado_sin_duplicados(self):
        adapter, fake = _construir_adapter()
        comision_a, comision_b = uuid4(), uuid4()
        estudiante_1 = EstudianteConEmail(id=uuid4(), nombre="Ana", email="ana@fiuner.edu.ar")
        estudiante_2 = EstudianteConEmail(id=uuid4(), nombre="Bruno", email="bruno@fiuner.edu.ar")
        fake.estudiantes_con_email_por_comision[comision_a] = [estudiante_1, estudiante_2]
        fake.estudiantes_con_email_por_comision[comision_b] = [estudiante_1]

        resultado = await adapter.listar_destinatarios([comision_a, comision_b])

        assert len(resultado) == 2
        assert {d.estudiante_id for d in resultado} == {estudiante_1.id, estudiante_2.id}

    async def test_comision_sin_estudiantes_devuelve_lista_vacia(self):
        adapter, _ = _construir_adapter()

        resultado = await adapter.listar_destinatarios([uuid4()])

        assert resultado == []
