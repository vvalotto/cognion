import pytest

from src.identidad.entities.errors import EmailYaRegistrado, PasswordDemasiadoCorta
from src.identidad.entities.eventos import UsuarioCreado
from src.identidad.use_cases.crear_usuario import CrearUsuarioUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import FakePasswordHasher, FakeUsuarioRepository


class TestCrearUsuarioUseCase:
    async def test_crea_usuario_con_password_hasheado(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        use_case = CrearUsuarioUseCase(repo, hasher)

        usuario, evento = await use_case.execute(
            "Ana", "ana@fiuner.edu.ar", "ClaveSegura#1", TipoPerfil.DOCENTE
        )

        assert usuario.password_hash == "hashed:ClaveSegura#1"
        assert usuario.password_hash != "ClaveSegura#1"
        assert isinstance(evento, UsuarioCreado)
        assert evento.usuario_id == usuario.id
        assert repo.usuarios[usuario.id] is usuario

    async def test_rechaza_email_duplicado(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        use_case = CrearUsuarioUseCase(repo, hasher)
        await use_case.execute("Ana", "ana@fiuner.edu.ar", "Clave#Segura1", TipoPerfil.DOCENTE)

        with pytest.raises(EmailYaRegistrado):
            await use_case.execute("Otro", "ana@fiuner.edu.ar", "Clave#Segura2", TipoPerfil.DOCENTE)

        assert len(repo.usuarios) == 1

    async def test_rechaza_password_debil_sin_crear_el_usuario(self):
        """Gap cerrado en US-ADJ-36: antes de esta US, este flujo no validaba INV-ID-11."""
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        use_case = CrearUsuarioUseCase(repo, hasher)

        with pytest.raises(PasswordDemasiadoCorta):
            await use_case.execute("Ana", "ana@fiuner.edu.ar", "abc123", TipoPerfil.DOCENTE)

        assert len(repo.usuarios) == 0
