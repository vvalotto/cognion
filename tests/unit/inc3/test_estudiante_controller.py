import uuid

from src.identidad.interface_adapters.controllers.estudiante_controller import (
    EstudianteController,
)
from src.identidad.use_cases.listar_materias_del_estudiante import (
    ListarMateriasDelEstudianteUseCase,
)
from tests.unit.inc1._fakes import FakeComisionRepository, FakeMateriaPort, FakeUsuarioRepository
from tests.unit.inc3.test_listar_materias_del_estudiante_use_case import (
    _crear_estudiante_con_comision,
)


class TestEstudianteController:
    async def test_listar_mis_materias_delega_en_el_use_case(self):
        usuario_repo = FakeUsuarioRepository()
        comision_repo = FakeComisionRepository()
        materia_port = FakeMateriaPort()
        materia_id = uuid.uuid4()
        estudiante = _crear_estudiante_con_comision(
            usuario_repo, comision_repo, materia_port, materia_id, "Ingeniería de Software"
        )
        controller = EstudianteController(
            ListarMateriasDelEstudianteUseCase(usuario_repo, comision_repo, materia_port)
        )

        resultado = await controller.listar_mis_materias(estudiante.id)

        assert len(resultado) == 1
        assert resultado[0].id == materia_id
