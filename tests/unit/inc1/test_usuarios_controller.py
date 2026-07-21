from src.identidad.entities.eventos import UsuarioCreado
from src.identidad.entities.usuario import TipoPerfil
from src.identidad.interface_adapters.controllers.usuarios_controller import UsuariosController
from src.identidad.use_cases.crear_usuario import CrearUsuarioUseCase
from tests.unit.inc1._fakes import FakePasswordHasher, FakeUsuarioRepository


class TestUsuariosController:
    async def test_crear_usuario_delega_al_use_case(self):
        repo = FakeUsuarioRepository()
        controller = UsuariosController(CrearUsuarioUseCase(repo, FakePasswordHasher()))

        usuario, evento = await controller.crear_usuario(
            "Ana", "ana@fiuner.edu.ar", "claveSegura1", TipoPerfil.DOCENTE
        )

        assert usuario.email == "ana@fiuner.edu.ar"
        assert isinstance(evento, UsuarioCreado)
        assert repo.usuarios[usuario.id] is usuario
