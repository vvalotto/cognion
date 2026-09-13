from src.identidad.entities.eventos import UsuarioAutoregistrado
from src.identidad.interface_adapters.controllers.autoregistro_controller import (
    AutoregistroController,
)
from src.identidad.use_cases.autoregistrar_docente import AutoregistrarDocenteUseCase
from tests.unit.inc1._fakes import FakePasswordHasher, FakeUsuarioRepository


class TestAutoregistroController:
    async def test_autoregistrar_docente_delega_al_use_case(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        controller = AutoregistroController(AutoregistrarDocenteUseCase(usuario_repo, hasher))

        usuario, evento = await controller.autoregistrar_docente(
            "Nico", "nico@fiuner.edu.ar", "Password#123x"
        )

        assert usuario.email == "nico@fiuner.edu.ar"
        assert isinstance(evento, UsuarioAutoregistrado)
