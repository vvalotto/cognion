import uuid

from src.identidad.entities.eventos import ComisionCreada, DocenteAsignado
from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.controllers.comisiones_controller import (
    ComisionesController,
)
from src.identidad.use_cases.activar_comision import ActivarComisionUseCase
from src.identidad.use_cases.asignar_docente_a_comision import AsignarDocenteAComisionUseCase
from src.identidad.use_cases.crear_comision import CrearComisionUseCase
from src.identidad.use_cases.editar_comision import EditarComisionUseCase
from src.identidad.use_cases.eliminar_comision import EliminarComisionUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import (
    FakeComisionQueryRepository,
    FakeComisionRepository,
    FakeMateriaPort,
    FakeUsuarioRepository,
)


def _controller(
    comision_repo: FakeComisionRepository,
    usuario_repo: FakeUsuarioRepository,
    materia_port: FakeMateriaPort,
) -> ComisionesController:
    comision_query = FakeComisionQueryRepository()
    return ComisionesController(
        CrearComisionUseCase(comision_repo, materia_port),
        AsignarDocenteAComisionUseCase(comision_repo, usuario_repo),
        EditarComisionUseCase(comision_repo),
        EliminarComisionUseCase(comision_repo, comision_query),
        ActivarComisionUseCase(comision_repo),
    )


class TestComisionesController:
    async def test_crear_comision_delega_al_use_case(self):
        comision_repo = FakeComisionRepository()
        usuario_repo = FakeUsuarioRepository()
        materia_port = FakeMateriaPort()
        materia_id = uuid.uuid4()
        materia_port.agregar(materia_id, "Ingeniería de Software")
        controller = _controller(comision_repo, usuario_repo, materia_port)

        comision, evento = await controller.crear_comision(materia_id, "lu 10-12", uuid.uuid4())

        assert comision.materia_id == materia_id
        assert comision.docentes_asignados == []
        assert isinstance(evento, ComisionCreada)

    async def test_asignar_docente_delega_al_use_case(self):
        comision_repo = FakeComisionRepository()
        usuario_repo = FakeUsuarioRepository()
        materia_port = FakeMateriaPort()
        materia_id = uuid.uuid4()
        materia_port.agregar(materia_id, "Ingeniería de Software")
        controller = _controller(comision_repo, usuario_repo, materia_port)
        docente = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        await usuario_repo.guardar(docente)
        comision, _ = await controller.crear_comision(materia_id, "lu 10-12", uuid.uuid4())

        resultado, evento = await controller.asignar_docente(comision.id, docente.id)

        assert docente.id in resultado.docentes_asignados
        assert isinstance(evento, DocenteAsignado)
