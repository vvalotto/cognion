from uuid import uuid4

from src.identidad.entities.comision import Comision
from src.identidad.entities.eventos import UsuarioAutoregistrado
from src.identidad.interface_adapters.controllers.autoregistro_controller import (
    AutoregistroController,
)
from src.identidad.use_cases.autoregistrar_docente import AutoregistrarDocenteUseCase
from src.identidad.use_cases.autoregistrar_estudiante import AutoregistrarEstudianteUseCase
from tests.unit.inc1._fakes import (
    FakeComisionRepository,
    FakePasswordHasher,
    FakeUsuarioRepository,
)


def _controller(usuario_repo=None, hasher=None, comision_repo=None) -> AutoregistroController:
    usuario_repo = usuario_repo or FakeUsuarioRepository()
    hasher = hasher or FakePasswordHasher()
    comision_repo = comision_repo or FakeComisionRepository()
    return AutoregistroController(
        AutoregistrarDocenteUseCase(usuario_repo, hasher),
        AutoregistrarEstudianteUseCase(usuario_repo, hasher, comision_repo),
    )


class TestAutoregistroController:
    async def test_autoregistrar_docente_delega_al_use_case(self):
        controller = _controller()

        usuario, evento = await controller.autoregistrar_docente(
            "Nico", "nico@fiuner.edu.ar", "Password#123x"
        )

        assert usuario.email == "nico@fiuner.edu.ar"
        assert isinstance(evento, UsuarioAutoregistrado)

    async def test_autoregistrar_estudiante_delega_al_use_case(self):
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(
            materia_id=uuid4(), horario="Lunes 10-12", administrador_id=uuid4()
        )
        await comision_repo.guardar(comision)
        controller = _controller(comision_repo=comision_repo)

        usuario, evento = await controller.autoregistrar_estudiante(
            "Vale", "vale@fiuner.edu.ar", "Password#123x", comision.id
        )

        assert usuario.email == "vale@fiuner.edu.ar"
        assert isinstance(evento, UsuarioAutoregistrado)
