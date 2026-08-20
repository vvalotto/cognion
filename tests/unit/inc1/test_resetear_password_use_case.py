import uuid

import pytest

from src.identidad.entities.errors import PasswordDemasiadoCorta, UsuarioNoExiste
from src.identidad.entities.eventos import CuentaDesbloqueada, PasswordReseteada
from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.resetear_password import ResetearPasswordUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import FakePasswordHasher, FakeUsuarioRepository


class TestResetearPasswordUseCase:
    async def test_actualiza_el_password_hash(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash-viejo", TipoPerfil.DOCENTE)
        repo.usuarios[usuario.id] = usuario
        use_case = ResetearPasswordUseCase(repo, hasher)
        administrador_id = uuid.uuid4()

        resultado, _evento_password, _evento_desbloqueo = await use_case.execute(
            usuario.id, "nuevaClave123", administrador_id
        )

        assert resultado.password_hash == hasher.hash("nuevaClave123")
        assert repo.usuarios[usuario.id].password_hash == hasher.hash("nuevaClave123")

    async def test_cuenta_bloqueada_se_desbloquea_y_emite_ambos_eventos(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        usuario.bloqueada = True
        usuario.intentos_fallidos_login = 3
        repo.usuarios[usuario.id] = usuario
        use_case = ResetearPasswordUseCase(repo, hasher)
        administrador_id = uuid.uuid4()

        resultado, evento_password, evento_desbloqueo = await use_case.execute(
            usuario.id, "nuevaClave123", administrador_id
        )

        assert resultado.bloqueada is False
        assert resultado.intentos_fallidos_login == 0
        assert isinstance(evento_password, PasswordReseteada)
        assert evento_password.usuario_id == usuario.id
        assert evento_password.administrador_id == administrador_id
        assert isinstance(evento_desbloqueo, CuentaDesbloqueada)
        assert evento_desbloqueo.usuario_id == usuario.id

    async def test_cuenta_activa_no_emite_cuenta_desbloqueada(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        repo.usuarios[usuario.id] = usuario
        use_case = ResetearPasswordUseCase(repo, hasher)
        administrador_id = uuid.uuid4()

        _resultado, evento_password, evento_desbloqueo = await use_case.execute(
            usuario.id, "nuevaClave123", administrador_id
        )

        assert isinstance(evento_password, PasswordReseteada)
        assert evento_desbloqueo is None

    async def test_rechaza_con_usuario_no_existe(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        use_case = ResetearPasswordUseCase(repo, hasher)
        usuario_id = uuid.uuid4()

        with pytest.raises(UsuarioNoExiste) as exc:
            await use_case.execute(usuario_id, "nuevaClave123", uuid.uuid4())

        assert exc.value.usuario_id == usuario_id

    async def test_rechaza_password_demasiado_corta_sin_modificar_el_usuario(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash-original", TipoPerfil.DOCENTE)
        repo.usuarios[usuario.id] = usuario
        use_case = ResetearPasswordUseCase(repo, hasher)

        with pytest.raises(PasswordDemasiadoCorta):
            await use_case.execute(usuario.id, "corta", uuid.uuid4())

        assert repo.usuarios[usuario.id].password_hash == "hash-original"
