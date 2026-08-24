import uuid

import pytest

from src.identidad.entities.errors import (
    CuentaBloqueadaError,
    PasswordActualIncorrecta,
    PasswordDemasiadoCorta,
    UsuarioNoExiste,
)
from src.identidad.entities.eventos import CuentaBloqueada, PasswordCambiada
from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.cambiar_password import CambiarPasswordUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import FakePasswordHasher, FakeUsuarioRepository


class TestCambiarPasswordUseCase:
    def _crear_usuario(self, hasher: FakePasswordHasher, **overrides: object) -> Usuario:
        usuario = Usuario.crear(
            "Ana", "ana@fiuner.edu.ar", hasher.hash("ClaveActual1"), TipoPerfil.DOCENTE
        )
        for campo, valor in overrides.items():
            setattr(usuario, campo, valor)
        return usuario

    async def test_cambio_exitoso_actualiza_hash_y_resetea_contador(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = self._crear_usuario(hasher, intentos_fallidos_password=1)
        repo.usuarios[usuario.id] = usuario
        use_case = CambiarPasswordUseCase(repo, hasher)

        evento = await use_case.execute(usuario.id, "ClaveActual1", "nuevaClave123")

        actualizado = repo.usuarios[usuario.id]
        assert actualizado.password_hash == hasher.hash("nuevaClave123")
        assert actualizado.intentos_fallidos_password == 0
        assert isinstance(evento, PasswordCambiada)
        assert evento.usuario_id == usuario.id

    async def test_rechaza_con_usuario_no_existe(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        use_case = CambiarPasswordUseCase(repo, hasher)
        usuario_id = uuid.uuid4()

        with pytest.raises(UsuarioNoExiste) as exc:
            await use_case.execute(usuario_id, "ClaveActual1", "nuevaClave123")

        assert exc.value.usuario_id == usuario_id

    async def test_cuenta_ya_bloqueada_rechaza_sin_verificar_password(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = self._crear_usuario(hasher, bloqueada=True, intentos_fallidos_password=3)
        repo.usuarios[usuario.id] = usuario
        use_case = CambiarPasswordUseCase(repo, hasher)

        with pytest.raises(CuentaBloqueadaError) as exc:
            await use_case.execute(usuario.id, "cualquier-cosa", "nuevaClave123")

        assert exc.value.usuario_id == usuario.id
        assert repo.usuarios[usuario.id].password_hash == hasher.hash("ClaveActual1")

    async def test_fallo_que_no_llega_al_limite(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = self._crear_usuario(hasher, intentos_fallidos_password=1)
        repo.usuarios[usuario.id] = usuario
        use_case = CambiarPasswordUseCase(repo, hasher)

        with pytest.raises(PasswordActualIncorrecta) as exc:
            await use_case.execute(usuario.id, "password-incorrecta", "nuevaClave123")

        actualizado = repo.usuarios[usuario.id]
        assert actualizado.intentos_fallidos_password == 2
        assert actualizado.bloqueada is False
        assert exc.value.evento_cuenta_bloqueada is None
        assert exc.value.intentos_restantes == 1

    async def test_tercer_fallo_consecutivo_bloquea_la_cuenta(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = self._crear_usuario(hasher, intentos_fallidos_password=2)
        repo.usuarios[usuario.id] = usuario
        use_case = CambiarPasswordUseCase(repo, hasher)

        with pytest.raises(PasswordActualIncorrecta) as exc:
            await use_case.execute(usuario.id, "password-incorrecta", "nuevaClave123")

        actualizado = repo.usuarios[usuario.id]
        assert actualizado.intentos_fallidos_password == 3
        assert actualizado.bloqueada is True
        assert isinstance(exc.value.evento_cuenta_bloqueada, CuentaBloqueada)
        assert exc.value.evento_cuenta_bloqueada.usuario_id == usuario.id
        assert exc.value.intentos_restantes == 0

    async def test_rechaza_password_nueva_demasiado_corta_sin_modificar_el_usuario(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = self._crear_usuario(hasher)
        repo.usuarios[usuario.id] = usuario
        use_case = CambiarPasswordUseCase(repo, hasher)

        with pytest.raises(PasswordDemasiadoCorta):
            await use_case.execute(usuario.id, "ClaveActual1", "corta")

        actualizado = repo.usuarios[usuario.id]
        assert actualizado.password_hash == hasher.hash("ClaveActual1")
        assert actualizado.intentos_fallidos_password == 0
