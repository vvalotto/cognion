from src.identidad.entities.eventos import SesionIniciada
from src.identidad.entities.usuario import TipoPerfil, Usuario
from src.identidad.interface_adapters.controllers.auth_controller import AuthController
from src.identidad.use_cases.iniciar_sesion import IniciarSesionUseCase
from tests.unit.inc1._fakes import FakeJWTIssuer, FakePasswordHasher, FakeUsuarioRepository


class TestAuthController:
    async def test_iniciar_sesion_delega_al_use_case(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        jwt_issuer = FakeJWTIssuer()
        usuario = Usuario.crear(
            "Docente", "docente@fiuner.edu.ar", hasher.hash("Docente#2026"), TipoPerfil.DOCENTE
        )
        usuario_repo.usuarios[usuario.id] = usuario

        controller = AuthController(IniciarSesionUseCase(usuario_repo, hasher, jwt_issuer))

        jwt_vo, evento = await controller.iniciar_sesion("docente@fiuner.edu.ar", "Docente#2026")

        assert jwt_vo.rol == TipoPerfil.DOCENTE
        assert isinstance(evento, SesionIniciada)
        assert evento.usuario_id == usuario.id
