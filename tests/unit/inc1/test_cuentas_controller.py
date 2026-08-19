from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.controllers.cuentas_controller import CuentasController
from src.identidad.use_cases.listar_cuentas import ListarCuentasUseCase
from src.identidad.use_cases.obtener_cuenta import ObtenerCuentaUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import FakeCuentaQueryRepository, FakeUsuarioRepository


class TestCuentasController:
    async def test_listar_cuentas_delega_en_el_use_case(self):
        cuenta_query_repo = FakeCuentaQueryRepository()
        usuario_repo = FakeUsuarioRepository()
        usuario = Usuario.crear("Docente", "docente@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        cuenta_query_repo.usuarios[usuario.id] = usuario
        controller = CuentasController(
            ListarCuentasUseCase(cuenta_query_repo), ObtenerCuentaUseCase(usuario_repo)
        )

        resultado = await controller.listar_cuentas(None, None, None)

        assert len(resultado) == 1
        assert resultado[0].id == usuario.id

    async def test_obtener_cuenta_delega_en_el_use_case(self):
        cuenta_query_repo = FakeCuentaQueryRepository()
        usuario_repo = FakeUsuarioRepository()
        usuario = Usuario.crear("Docente", "docente@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        usuario_repo.usuarios[usuario.id] = usuario
        controller = CuentasController(
            ListarCuentasUseCase(cuenta_query_repo), ObtenerCuentaUseCase(usuario_repo)
        )

        resultado = await controller.obtener_cuenta(usuario.id)

        assert resultado.id == usuario.id
