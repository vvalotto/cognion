from src.identidad.interface_adapters.controllers.usuarios_controller import UsuariosController
from src.identidad.use_cases.crear_usuario import CrearUsuarioUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import FakePasswordHasher, FakeUsuarioRepository


class TestUsuariosController:
    async def test_crear_usuario_delega_al_use_case(self):
        repo = FakeUsuarioRepository()
        controller = UsuariosController(CrearUsuarioUseCase(repo, FakePasswordHasher()))

        salida = await controller.crear_usuario(
            "Ana", "ana@fiuner.edu.ar", "claveSegura1#", TipoPerfil.DOCENTE
        )

        assert salida.email == "ana@fiuner.edu.ar"
        assert repo.usuarios[salida.id].email == "ana@fiuner.edu.ar"
