from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.controllers.cuentas_controller import CuentasController
from src.identidad.use_cases.listar_cuentas import ListarCuentasUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import FakeCuentaQueryRepository


class TestCuentasController:
    async def test_listar_cuentas_delega_en_el_use_case(self):
        repo = FakeCuentaQueryRepository()
        usuario = Usuario.crear("Docente", "docente@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        repo.usuarios[usuario.id] = usuario
        controller = CuentasController(ListarCuentasUseCase(repo))

        resultado = await controller.listar_cuentas(None, None, None)

        assert len(resultado) == 1
        assert resultado[0].id == usuario.id
