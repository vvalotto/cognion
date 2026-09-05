"""Tests unitarios de `ComisionesQueryController` (US-4.2.2)."""

from uuid import UUID, uuid4

import pytest

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import ComisionNoExiste, MateriaNoExiste
from src.identidad.entities.ports.comision_query_port import ComisionQueryPort, EstudianteResumen
from src.identidad.interface_adapters.controllers.comisiones_query_controller import (
    ComisionesQueryController,
)
from tests.unit.inc1._fakes import FakeComisionRepository, FakeMateriaPort


class _ComisionQueryPortFake(ComisionQueryPort):
    def __init__(self) -> None:
        self.comisiones_por_materia: dict[UUID, list[Comision]] = {}
        self.estudiantes_por_comision: dict[UUID, list[EstudianteResumen]] = {}

    async def listar_comisiones_por_materia(self, materia_id: UUID) -> list[Comision]:
        return self.comisiones_por_materia.get(materia_id, [])

    async def listar_estudiantes(self, comision_id: UUID) -> list[EstudianteResumen]:
        return self.estudiantes_por_comision.get(comision_id, [])


class TestListarComisionesPorMateria:
    @pytest.mark.asyncio
    async def test_materia_con_comisiones(self):
        materia_id = uuid4()
        comision_query = _ComisionQueryPortFake()
        comision = Comision.crear(materia_id, "lu 10-12", uuid4())
        comision_query.comisiones_por_materia[materia_id] = [comision]
        materia_port = FakeMateriaPort()
        materia_port.agregar(materia_id, "Ingeniería de Software")
        controller = ComisionesQueryController(
            comision_query, materia_port, FakeComisionRepository()
        )

        resultado = await controller.listar_comisiones_por_materia(materia_id)

        assert resultado == [comision]

    @pytest.mark.asyncio
    async def test_materia_inexistente_levanta_error(self):
        materia_id = uuid4()
        controller = ComisionesQueryController(
            _ComisionQueryPortFake(), FakeMateriaPort(), FakeComisionRepository()
        )

        with pytest.raises(MateriaNoExiste):
            await controller.listar_comisiones_por_materia(materia_id)


class TestListarEstudiantes:
    @pytest.mark.asyncio
    async def test_comision_con_estudiantes(self):
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        await comision_repo.guardar(comision)
        comision_query = _ComisionQueryPortFake()
        estudiante = EstudianteResumen(id=uuid4(), nombre="Ana Pérez")
        comision_query.estudiantes_por_comision[comision.id] = [estudiante]
        controller = ComisionesQueryController(comision_query, FakeMateriaPort(), comision_repo)

        resultado = await controller.listar_estudiantes(comision.id)

        assert resultado == [estudiante]

    @pytest.mark.asyncio
    async def test_comision_sin_estudiantes(self):
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        await comision_repo.guardar(comision)
        controller = ComisionesQueryController(
            _ComisionQueryPortFake(), FakeMateriaPort(), comision_repo
        )

        resultado = await controller.listar_estudiantes(comision.id)

        assert resultado == []

    @pytest.mark.asyncio
    async def test_comision_inexistente_levanta_error(self):
        controller = ComisionesQueryController(
            _ComisionQueryPortFake(), FakeMateriaPort(), FakeComisionRepository()
        )

        with pytest.raises(ComisionNoExiste):
            await controller.listar_estudiantes(uuid4())
