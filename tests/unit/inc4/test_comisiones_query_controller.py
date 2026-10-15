"""Tests unitarios de `ComisionesQueryController` (US-4.2.2)."""

from uuid import UUID, uuid4

import pytest

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import (
    ComisionNoAutorizada,
    ComisionNoExiste,
    MateriaNoAutorizada,
    MateriaNoExiste,
)
from src.identidad.entities.ports.comision_query_port import (
    ComisionQueryPort,
    EstudianteConEmail,
    EstudianteResumen,
)
from src.identidad.interface_adapters.controllers.comisiones_query_controller import (
    ComisionesQueryController,
)
from tests.unit.inc1._fakes import FakeComisionRepository, FakeMateriaPort


class _ComisionQueryPortFake(ComisionQueryPort):
    def __init__(self) -> None:
        self.comisiones_por_materia: dict[UUID, list[Comision]] = {}
        self.estudiantes_por_comision: dict[UUID, list[EstudianteResumen]] = {}

    async def listar_comisiones_por_materia(
        self, materia_id: UUID, incluir_inactivas: bool = False
    ) -> list[Comision]:
        return self.comisiones_por_materia.get(materia_id, [])

    async def listar_estudiantes(self, comision_id: UUID) -> list[EstudianteResumen]:
        return self.estudiantes_por_comision.get(comision_id, [])

    async def listar_estudiantes_con_email(self, comision_id: UUID) -> list[EstudianteConEmail]:
        return []

    async def tiene_comisiones_asignadas(self, docente_id: UUID) -> bool:
        return False

    async def docente_pertenece_a_comision(self, docente_id: UUID, comision_id: UUID) -> bool:
        for comisiones in self.comisiones_por_materia.values():
            for comision in comisiones:
                if comision.id == comision_id:
                    return docente_id in comision.docentes_asignados
        return False

    async def docente_tiene_comision_en_materia(self, docente_id: UUID, materia_id: UUID) -> bool:
        return any(
            docente_id in comision.docentes_asignados
            for comision in self.comisiones_por_materia.get(materia_id, [])
        )


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

    @pytest.mark.asyncio
    async def test_docente_ve_solo_sus_comisiones(self):
        """`US-ADJ-57`: con `docente_id`, el resultado se acota a las comisiones propias."""
        materia_id = uuid4()
        docente_id = uuid4()
        propia = Comision.crear(materia_id, "lu 10-12", uuid4())
        propia.asignar_docente(docente_id)
        ajena = Comision.crear(materia_id, "ma 14-16", uuid4())
        ajena.asignar_docente(uuid4())
        comision_query = _ComisionQueryPortFake()
        comision_query.comisiones_por_materia[materia_id] = [propia, ajena]
        materia_port = FakeMateriaPort()
        materia_port.agregar(materia_id, "Ingeniería de Software")
        controller = ComisionesQueryController(
            comision_query, materia_port, FakeComisionRepository()
        )

        resultado = await controller.listar_comisiones_por_materia(
            materia_id, docente_id=docente_id
        )

        assert resultado == [propia]

    @pytest.mark.asyncio
    async def test_docente_sin_ninguna_comision_en_la_materia_403(self):
        materia_id = uuid4()
        ajena = Comision.crear(materia_id, "ma 14-16", uuid4())
        ajena.asignar_docente(uuid4())
        comision_query = _ComisionQueryPortFake()
        comision_query.comisiones_por_materia[materia_id] = [ajena]
        materia_port = FakeMateriaPort()
        materia_port.agregar(materia_id, "Ingeniería de Software")
        controller = ComisionesQueryController(
            comision_query, materia_port, FakeComisionRepository()
        )

        with pytest.raises(MateriaNoAutorizada):
            await controller.listar_comisiones_por_materia(materia_id, docente_id=uuid4())

    @pytest.mark.asyncio
    async def test_administrador_ve_todas_sin_filtrar(self):
        """`docente_id=None` (Administrador) — sin cambios respecto del comportamiento previo."""
        materia_id = uuid4()
        comision_a = Comision.crear(materia_id, "lu 10-12", uuid4())
        comision_a.asignar_docente(uuid4())
        comision_b = Comision.crear(materia_id, "ma 14-16", uuid4())
        comision_query = _ComisionQueryPortFake()
        comision_query.comisiones_por_materia[materia_id] = [comision_a, comision_b]
        materia_port = FakeMateriaPort()
        materia_port.agregar(materia_id, "Ingeniería de Software")
        controller = ComisionesQueryController(
            comision_query, materia_port, FakeComisionRepository()
        )

        resultado = await controller.listar_comisiones_por_materia(materia_id, docente_id=None)

        assert resultado == [comision_a, comision_b]


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

    @pytest.mark.asyncio
    async def test_docente_no_asignado_403(self):
        """`US-ADJ-57`: el Docente que llama debe estar asignado a esta comisión puntual."""
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        comision.asignar_docente(uuid4())
        await comision_repo.guardar(comision)
        controller = ComisionesQueryController(
            _ComisionQueryPortFake(), FakeMateriaPort(), comision_repo
        )

        with pytest.raises(ComisionNoAutorizada):
            await controller.listar_estudiantes(comision.id, docente_id=uuid4())

    @pytest.mark.asyncio
    async def test_docente_asignado_ve_el_roster(self):
        comision_repo = FakeComisionRepository()
        docente_id = uuid4()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        comision.asignar_docente(docente_id)
        await comision_repo.guardar(comision)
        controller = ComisionesQueryController(
            _ComisionQueryPortFake(), FakeMateriaPort(), comision_repo
        )

        resultado = await controller.listar_estudiantes(comision.id, docente_id=docente_id)

        assert resultado == []


class TestObtenerComision:
    """`US-ADJ-25`: consulta de lectura simple sobre `ComisionRepositoryPort`."""

    @pytest.mark.asyncio
    async def test_comision_existente(self):
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        await comision_repo.guardar(comision)
        controller = ComisionesQueryController(
            _ComisionQueryPortFake(), FakeMateriaPort(), comision_repo
        )

        resultado = await controller.obtener_comision(comision.id)

        assert resultado == comision

    @pytest.mark.asyncio
    async def test_comision_inexistente_levanta_error(self):
        controller = ComisionesQueryController(
            _ComisionQueryPortFake(), FakeMateriaPort(), FakeComisionRepository()
        )

        with pytest.raises(ComisionNoExiste):
            await controller.obtener_comision(uuid4())

    @pytest.mark.asyncio
    async def test_docente_no_asignado_403(self):
        """`US-ADJ-57`: el Docente que llama debe estar asignado a esta comisión puntual."""
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        comision.asignar_docente(uuid4())
        await comision_repo.guardar(comision)
        controller = ComisionesQueryController(
            _ComisionQueryPortFake(), FakeMateriaPort(), comision_repo
        )

        with pytest.raises(ComisionNoAutorizada):
            await controller.obtener_comision(comision.id, docente_id=uuid4())
