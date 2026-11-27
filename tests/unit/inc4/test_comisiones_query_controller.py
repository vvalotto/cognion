"""Tests unitarios de `ComisionesQueryController` (US-4.2.2).

Desde `US-12.2.4` el controller solo delega y presenta; las reglas (existencia de la materia o la
comisión y autorización del Docente) se prueban en `tests/unit/inc12/test_casos_de_uso_de_comisiones_y_registro.py`.
"""

from uuid import UUID, uuid4

import pytest

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import ComisionNoAutorizada, ComisionNoExiste, MateriaNoExiste
from src.identidad.entities.ports.comision_query_port import EstudianteResumen
from src.identidad.interface_adapters.controllers.comisiones_query_controller import (
    ComisionesQueryController,
)
from src.identidad.interface_adapters.presenters.identidad_presenter import (
    ComisionResumenSalida,
    ComisionSalida,
    EstudianteResumenSalida,
)
from src.identidad.use_cases.listar_comisiones_de_materia import ListarComisionesDeMateriaUseCase
from src.identidad.use_cases.listar_estudiantes_de_comision import (
    ListarEstudiantesDeComisionUseCase,
)
from src.identidad.use_cases.obtener_comision import ObtenerComisionUseCase
from tests.unit.inc1._fakes import FakeComisionRepository, FakeMateriaPort
from tests.unit.inc12.test_casos_de_uso_de_comisiones_y_registro import _ComisionQueryPortFake


def _controller(
    comision_query: _ComisionQueryPortFake | None = None,
    materia_port: FakeMateriaPort | None = None,
    comision_repo: FakeComisionRepository | None = None,
) -> ComisionesQueryController:
    comision_query = comision_query or _ComisionQueryPortFake()
    materia_port = materia_port or FakeMateriaPort()
    comision_repo = comision_repo or FakeComisionRepository()
    return ComisionesQueryController(
        ListarComisionesDeMateriaUseCase(comision_query, materia_port),
        ListarEstudiantesDeComisionUseCase(comision_repo, comision_query),
        ObtenerComisionUseCase(comision_repo),
    )


class TestComisionesQueryController:
    @pytest.mark.asyncio
    async def test_lista_las_comisiones_de_la_materia_presentadas(self):
        materia_id: UUID = uuid4()
        comision = Comision.crear(materia_id, "lu 10-12", uuid4())
        comision_query = _ComisionQueryPortFake()
        comision_query.comisiones_por_materia[materia_id] = [comision]
        materia_port = FakeMateriaPort()
        materia_port.agregar(materia_id, "Ingeniería de Software")

        resultado = await _controller(comision_query, materia_port).listar_comisiones_por_materia(
            materia_id
        )

        assert resultado == [
            ComisionResumenSalida(comision.id, "lu 10-12", comision.docentes_asignados, True)
        ]

    @pytest.mark.asyncio
    async def test_materia_inexistente_levanta_el_error_del_caso_de_uso(self):
        with pytest.raises(MateriaNoExiste):
            await _controller().listar_comisiones_por_materia(uuid4())

    @pytest.mark.asyncio
    async def test_lista_los_estudiantes_presentados(self):
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        await comision_repo.guardar(comision)
        comision_query = _ComisionQueryPortFake()
        estudiante = EstudianteResumen(id=uuid4(), nombre="Ana Pérez")
        comision_query.estudiantes_por_comision[comision.id] = [estudiante]

        resultado = await _controller(
            comision_query, comision_repo=comision_repo
        ).listar_estudiantes(comision.id)

        assert resultado == [EstudianteResumenSalida(estudiante.id, "Ana Pérez")]

    @pytest.mark.asyncio
    async def test_obtener_comision_la_presenta(self):
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        await comision_repo.guardar(comision)

        resultado = await _controller(comision_repo=comision_repo).obtener_comision(comision.id)

        assert resultado == ComisionSalida(
            comision.id,
            comision.materia_id,
            "lu 10-12",
            comision.administrador_id,
            comision.docentes_asignados,
            True,
        )

    @pytest.mark.asyncio
    async def test_comision_inexistente_o_ajena_levanta_los_errores_del_caso_de_uso(self):
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
        comision.asignar_docente(uuid4())
        await comision_repo.guardar(comision)
        controller = _controller(comision_repo=comision_repo)

        with pytest.raises(ComisionNoExiste):
            await controller.obtener_comision(uuid4())
        with pytest.raises(ComisionNoAutorizada):
            await controller.listar_estudiantes(comision.id, docente_id=uuid4())
