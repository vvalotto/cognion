import uuid

from src.identidad.entities.usuario import Docente, Usuario
from src.identidad.interface_adapters.controllers.recuperacion_password_controller import (
    RecuperacionPasswordController,
)
from src.identidad.use_cases.solicitar_recuperacion_password import (
    SolicitarRecuperacionPasswordUseCase,
)
from tests.unit.inc1._fakes import (
    FakeCanalRecuperacion,
    FakeTokenRecuperacionPasswordRepository,
    FakeUsuarioRepository,
)


class TestRecuperacionPasswordController:
    async def test_solicitar_delega_al_use_case(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        canal = FakeCanalRecuperacion()
        usuario_id = uuid.uuid4()
        usuario = Usuario(
            id=usuario_id,
            nombre="Docente",
            email="docente@fiuner.edu.ar",
            password_hash="hash",
            perfil=Docente(id=usuario_id),
        )
        await usuario_repo.guardar(usuario)

        controller = RecuperacionPasswordController(
            SolicitarRecuperacionPasswordUseCase(usuario_repo, token_repo, canal)
        )

        await controller.solicitar("docente@fiuner.edu.ar")

        assert len(token_repo.tokens) == 1
        assert len(canal.enviados) == 1

    async def test_solicitar_con_email_inexistente_no_falla(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        canal = FakeCanalRecuperacion()

        controller = RecuperacionPasswordController(
            SolicitarRecuperacionPasswordUseCase(usuario_repo, token_repo, canal)
        )

        await controller.solicitar("inexistente@fiuner.edu.ar")

        assert token_repo.tokens == {}
        assert canal.enviados == []
