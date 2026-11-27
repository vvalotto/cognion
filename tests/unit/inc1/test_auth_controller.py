from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.controllers.auth_controller import AuthController
from src.identidad.use_cases.iniciar_sesion import IniciarSesionUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
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

        salida = await controller.iniciar_sesion("docente@fiuner.edu.ar", "Docente#2026")

        assert salida.rol == TipoPerfil.DOCENTE
        assert salida.token_type == "bearer"
        assert salida.access_token
