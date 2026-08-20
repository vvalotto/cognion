import uuid

from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.controllers.cuentas_controller import CuentasController
from src.identidad.use_cases.listar_cuentas import ListarCuentasUseCase
from src.identidad.use_cases.obtener_cuenta import ObtenerCuentaUseCase
from src.identidad.use_cases.resetear_password import ResetearPasswordUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import (
    FakeCuentaQueryRepository,
    FakePasswordHasher,
    FakeUsuarioRepository,
)


def _armar_controller(
    cuenta_query_repo: FakeCuentaQueryRepository, usuario_repo: FakeUsuarioRepository
) -> CuentasController:
    return CuentasController(
        ListarCuentasUseCase(cuenta_query_repo),
        ObtenerCuentaUseCase(usuario_repo),
        ResetearPasswordUseCase(usuario_repo, FakePasswordHasher()),
    )


class TestCuentasController:
    async def test_listar_cuentas_delega_en_el_use_case(self):
        cuenta_query_repo = FakeCuentaQueryRepository()
        usuario_repo = FakeUsuarioRepository()
        usuario = Usuario.crear("Docente", "docente@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        cuenta_query_repo.usuarios[usuario.id] = usuario
        controller = _armar_controller(cuenta_query_repo, usuario_repo)

        resultado = await controller.listar_cuentas(None, None, None)

        assert len(resultado) == 1
        assert resultado[0].id == usuario.id

    async def test_obtener_cuenta_delega_en_el_use_case(self):
        cuenta_query_repo = FakeCuentaQueryRepository()
        usuario_repo = FakeUsuarioRepository()
        usuario = Usuario.crear("Docente", "docente@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        usuario_repo.usuarios[usuario.id] = usuario
        controller = _armar_controller(cuenta_query_repo, usuario_repo)

        resultado = await controller.obtener_cuenta(usuario.id)

        assert resultado.id == usuario.id

    async def test_resetear_password_delega_en_el_use_case(self):
        cuenta_query_repo = FakeCuentaQueryRepository()
        usuario_repo = FakeUsuarioRepository()
        usuario = Usuario.crear(
            "Docente", "docente@fiuner.edu.ar", "hash-viejo", TipoPerfil.DOCENTE
        )
        usuario.bloqueada = True
        usuario_repo.usuarios[usuario.id] = usuario
        controller = _armar_controller(cuenta_query_repo, usuario_repo)

        resultado = await controller.resetear_password(usuario.id, "nuevaClave123", uuid.uuid4())

        assert resultado.id == usuario.id
        assert resultado.bloqueada is False
        assert resultado.password_hash != "hash-viejo"
