import pytest

from src.identidad.entities.errors import EmailYaRegistrado, PasswordDemasiadoCorta
from src.identidad.entities.eventos import UsuarioAutoregistrado
from src.identidad.entities.usuario import Docente
from src.identidad.use_cases.autoregistrar_docente import AutoregistrarDocenteUseCase
from tests.unit.inc1._fakes import FakePasswordHasher, FakeUsuarioRepository


class TestAutoregistrarDocenteUseCase:
    async def test_crea_docente_activo_con_password_hasheado(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        use_case = AutoregistrarDocenteUseCase(repo, hasher)

        usuario, evento = await use_case.execute("Ana", "ana@fiuner.edu.ar", "ClaveSegura#1")

        assert usuario.password_hash == "hashed:ClaveSegura#1"
        assert usuario.password_hash != "ClaveSegura#1"
        assert isinstance(usuario.perfil, Docente)
        assert usuario.bloqueada is False
        assert isinstance(evento, UsuarioAutoregistrado)
        assert evento.usuario_id == usuario.id
        assert repo.usuarios[usuario.id] is usuario

    async def test_rechaza_email_duplicado(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        use_case = AutoregistrarDocenteUseCase(repo, hasher)
        await use_case.execute("Ana", "ana@fiuner.edu.ar", "Clave#Segura1")

        with pytest.raises(EmailYaRegistrado):
            await use_case.execute("Otro", "ana@fiuner.edu.ar", "Clave#Segura2")

        assert len(repo.usuarios) == 1

    async def test_rechaza_password_debil_sin_crear_el_usuario(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        use_case = AutoregistrarDocenteUseCase(repo, hasher)

        with pytest.raises(PasswordDemasiadoCorta):
            await use_case.execute("Ana", "ana@fiuner.edu.ar", "abc123")

        assert len(repo.usuarios) == 0
