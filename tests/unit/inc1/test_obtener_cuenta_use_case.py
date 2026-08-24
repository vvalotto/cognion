import uuid

import pytest

from src.identidad.entities.errors import UsuarioNoExiste
from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.obtener_cuenta import ObtenerCuentaUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import FakeUsuarioRepository


class TestObtenerCuentaUseCase:
    async def test_devuelve_el_detalle_de_un_docente(self):
        repo = FakeUsuarioRepository()
        usuario = Usuario.crear("Docente", "docente@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        repo.usuarios[usuario.id] = usuario
        use_case = ObtenerCuentaUseCase(repo)

        resultado = await use_case.execute(usuario.id)

        assert resultado.id == usuario.id
        assert resultado.tipo_perfil == TipoPerfil.DOCENTE

    async def test_devuelve_el_detalle_de_un_estudiante_con_comision(self):
        repo = FakeUsuarioRepository()
        comision_id = uuid.uuid4()
        usuario = Usuario.crear_estudiante(
            "Estudiante", "estudiante@fiuner.edu.ar", "hash", comision_id
        )
        repo.usuarios[usuario.id] = usuario
        use_case = ObtenerCuentaUseCase(repo)

        resultado = await use_case.execute(usuario.id)

        assert resultado.tipo_perfil == TipoPerfil.ESTUDIANTE
        assert resultado.perfil.comision_id == comision_id

    async def test_rechaza_con_usuario_no_existe(self):
        repo = FakeUsuarioRepository()
        use_case = ObtenerCuentaUseCase(repo)
        usuario_id = uuid.uuid4()

        with pytest.raises(UsuarioNoExiste) as exc:
            await use_case.execute(usuario_id)

        assert exc.value.usuario_id == usuario_id
