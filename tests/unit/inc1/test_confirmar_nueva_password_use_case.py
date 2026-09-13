import uuid
from datetime import UTC, datetime, timedelta

import pytest

from src.identidad.entities.errors import (
    PasswordDemasiadoCorta,
    TokenRecuperacionInvalido,
    TokenRecuperacionVencido,
    TokenRecuperacionYaUsado,
    UsuarioNoExiste,
)
from src.identidad.entities.token_recuperacion_password import TokenRecuperacionPassword
from src.identidad.entities.usuario import Docente, Usuario
from src.identidad.use_cases.confirmar_nueva_password import ConfirmarNuevaPasswordUseCase
from tests.unit.inc1._fakes import (
    FakePasswordHasher,
    FakeTokenRecuperacionPasswordRepository,
    FakeUsuarioRepository,
)


def _usuario(email: str = "docente@fiuner.edu.ar") -> Usuario:
    usuario_id = uuid.uuid4()
    return Usuario(
        id=usuario_id,
        nombre="Docente de Prueba",
        email=email,
        password_hash="hash-viejo",
        perfil=Docente(id=usuario_id),
    )


class TestConfirmarNuevaPasswordUseCase:
    async def test_actualiza_el_password_hash_con_token_vigente(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        hasher = FakePasswordHasher()
        usuario = _usuario()
        await usuario_repo.guardar(usuario)
        token = TokenRecuperacionPassword.crear(usuario.id)
        await token_repo.guardar(token)

        use_case = ConfirmarNuevaPasswordUseCase(usuario_repo, token_repo, hasher)
        usuario_actualizado, evento = await use_case.execute(token.token, "Segura#2026x")

        assert usuario_actualizado.password_hash == "hashed:Segura#2026x"
        assert evento.usuario_id == usuario.id

    async def test_marca_el_token_como_usado(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        hasher = FakePasswordHasher()
        usuario = _usuario()
        await usuario_repo.guardar(usuario)
        token = TokenRecuperacionPassword.crear(usuario.id)
        await token_repo.guardar(token)

        use_case = ConfirmarNuevaPasswordUseCase(usuario_repo, token_repo, hasher)
        await use_case.execute(token.token, "Segura#2026x")

        assert token.usado_en is not None

    async def test_token_ya_usado_lanza_ya_usado_y_no_cambia_el_hash(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        hasher = FakePasswordHasher()
        usuario = _usuario()
        await usuario_repo.guardar(usuario)
        token = TokenRecuperacionPassword.crear(usuario.id)
        token.invalidar(datetime.now(UTC))
        await token_repo.guardar(token)

        use_case = ConfirmarNuevaPasswordUseCase(usuario_repo, token_repo, hasher)
        with pytest.raises(TokenRecuperacionYaUsado):
            await use_case.execute(token.token, "Segura#2026x")

        assert usuario.password_hash == "hash-viejo"

    async def test_token_vencido_lanza_vencido(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        hasher = FakePasswordHasher()
        usuario = _usuario()
        await usuario_repo.guardar(usuario)
        token = TokenRecuperacionPassword.crear(usuario.id)
        token.expira_en = datetime.now(UTC) - timedelta(seconds=1)
        await token_repo.guardar(token)

        use_case = ConfirmarNuevaPasswordUseCase(usuario_repo, token_repo, hasher)
        with pytest.raises(TokenRecuperacionVencido):
            await use_case.execute(token.token, "Segura#2026x")

    async def test_token_de_usuario_inexistente_lanza_usuario_no_existe(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        hasher = FakePasswordHasher()
        token = TokenRecuperacionPassword.crear(uuid.uuid4())
        await token_repo.guardar(token)

        use_case = ConfirmarNuevaPasswordUseCase(usuario_repo, token_repo, hasher)
        with pytest.raises(UsuarioNoExiste):
            await use_case.execute(token.token, "Segura#2026x")

    async def test_token_inexistente_lanza_invalido(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        hasher = FakePasswordHasher()

        use_case = ConfirmarNuevaPasswordUseCase(usuario_repo, token_repo, hasher)
        with pytest.raises(TokenRecuperacionInvalido):
            await use_case.execute("token-inexistente", "Segura#2026x")

    async def test_password_invalida_no_cambia_el_hash_ni_marca_el_token(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        hasher = FakePasswordHasher()
        usuario = _usuario()
        await usuario_repo.guardar(usuario)
        token = TokenRecuperacionPassword.crear(usuario.id)
        await token_repo.guardar(token)

        use_case = ConfirmarNuevaPasswordUseCase(usuario_repo, token_repo, hasher)
        with pytest.raises(PasswordDemasiadoCorta):
            await use_case.execute(token.token, "corta")

        assert usuario.password_hash == "hash-viejo"
        assert token.usado_en is None

    async def test_no_desbloquea_una_cuenta_bloqueada(self):
        usuario_repo = FakeUsuarioRepository()
        token_repo = FakeTokenRecuperacionPasswordRepository()
        hasher = FakePasswordHasher()
        usuario = _usuario()
        usuario.bloqueada = True
        await usuario_repo.guardar(usuario)
        token = TokenRecuperacionPassword.crear(usuario.id)
        await token_repo.guardar(token)

        use_case = ConfirmarNuevaPasswordUseCase(usuario_repo, token_repo, hasher)
        usuario_actualizado, _evento = await use_case.execute(token.token, "Segura#2026x")

        assert usuario_actualizado.password_hash == "hashed:Segura#2026x"
        assert usuario_actualizado.bloqueada is True
