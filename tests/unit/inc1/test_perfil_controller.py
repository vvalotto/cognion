from src.identidad.entities.eventos import PasswordCambiada
from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.controllers.perfil_controller import PerfilController
from src.identidad.use_cases.cambiar_password import CambiarPasswordUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import FakePasswordHasher, FakeUsuarioRepository


class TestPerfilController:
    async def test_cambiar_password_delega_en_el_use_case(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = Usuario.crear(
            "Docente", "docente@fiuner.edu.ar", hasher.hash("ClaveActual1"), TipoPerfil.DOCENTE
        )
        usuario_repo.usuarios[usuario.id] = usuario
        controller = PerfilController(CambiarPasswordUseCase(usuario_repo, hasher))

        resultado = await controller.cambiar_password(usuario.id, "ClaveActual1", "nuevaClave123")

        assert isinstance(resultado, PasswordCambiada)
        assert resultado.usuario_id == usuario.id
        assert usuario_repo.usuarios[usuario.id].password_hash == hasher.hash("nuevaClave123")
