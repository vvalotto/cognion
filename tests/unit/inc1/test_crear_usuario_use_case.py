import pytest

from src.identidad.entities.errors import EmailYaRegistrado
from src.identidad.entities.eventos import UsuarioCreado
from src.identidad.entities.usuario import TipoPerfil
from src.identidad.use_cases.crear_usuario import CrearUsuarioUseCase
from tests.unit.inc1._fakes import FakePasswordHasher, FakeUsuarioRepository


class TestCrearUsuarioUseCase:
    async def test_crea_usuario_con_password_hasheado(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        use_case = CrearUsuarioUseCase(repo, hasher)

        usuario, evento = await use_case.execute(
            "Ana", "ana@fiuner.edu.ar", "claveSegura1", TipoPerfil.DOCENTE
        )

        assert usuario.password_hash == "hashed:claveSegura1"
        assert usuario.password_hash != "claveSegura1"
        assert isinstance(evento, UsuarioCreado)
        assert evento.usuario_id == usuario.id
        assert repo.usuarios[usuario.id] is usuario

    async def test_rechaza_email_duplicado(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        use_case = CrearUsuarioUseCase(repo, hasher)
        await use_case.execute("Ana", "ana@fiuner.edu.ar", "clave1", TipoPerfil.DOCENTE)

        with pytest.raises(EmailYaRegistrado):
            await use_case.execute("Otro", "ana@fiuner.edu.ar", "clave2", TipoPerfil.DOCENTE)

        assert len(repo.usuarios) == 1
