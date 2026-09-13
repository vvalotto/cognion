from uuid import uuid4

import pytest

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import (
    ComisionNoExiste,
    EmailYaRegistrado,
    PasswordDemasiadoCorta,
)
from src.identidad.entities.eventos import UsuarioAutoregistrado
from src.identidad.entities.usuario import Estudiante
from src.identidad.use_cases.autoregistrar_estudiante import AutoregistrarEstudianteUseCase
from tests.unit.inc1._fakes import (
    FakeComisionRepository,
    FakePasswordHasher,
    FakeUsuarioRepository,
)


def _comision() -> Comision:
    return Comision.crear(materia_id=uuid4(), horario="Lunes 10-12", administrador_id=uuid4())


class TestAutoregistrarEstudianteUseCase:
    async def test_crea_estudiante_activo_asignado_a_su_comision(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        comision_repo = FakeComisionRepository()
        comision = _comision()
        await comision_repo.guardar(comision)
        use_case = AutoregistrarEstudianteUseCase(repo, hasher, comision_repo)

        usuario, evento = await use_case.execute(
            "Ana", "ana.estudiante@fiuner.edu.ar", "ClaveSegura#1", comision.id
        )

        assert usuario.password_hash == "hashed:ClaveSegura#1"
        assert usuario.password_hash != "ClaveSegura#1"
        assert isinstance(usuario.perfil, Estudiante)
        assert usuario.perfil.comision_id == comision.id
        assert usuario.bloqueada is False
        assert isinstance(evento, UsuarioAutoregistrado)
        assert evento.usuario_id == usuario.id
        assert repo.usuarios[usuario.id] is usuario

    async def test_rechaza_email_duplicado(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        comision_repo = FakeComisionRepository()
        comision = _comision()
        await comision_repo.guardar(comision)
        use_case = AutoregistrarEstudianteUseCase(repo, hasher, comision_repo)
        await use_case.execute(
            "Ana", "ana.estudiante@fiuner.edu.ar", "Clave#Segura1", comision.id
        )

        with pytest.raises(EmailYaRegistrado):
            await use_case.execute(
                "Otra", "ana.estudiante@fiuner.edu.ar", "Clave#Segura2", comision.id
            )

        assert len(repo.usuarios) == 1

    async def test_rechaza_comision_inexistente_sin_crear_el_usuario(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        comision_repo = FakeComisionRepository()
        use_case = AutoregistrarEstudianteUseCase(repo, hasher, comision_repo)

        with pytest.raises(ComisionNoExiste):
            await use_case.execute(
                "Ana", "ana.estudiante@fiuner.edu.ar", "Clave#Segura1", uuid4()
            )

        assert len(repo.usuarios) == 0

    async def test_rechaza_password_debil_sin_crear_el_usuario(self):
        repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        comision_repo = FakeComisionRepository()
        comision = _comision()
        await comision_repo.guardar(comision)
        use_case = AutoregistrarEstudianteUseCase(repo, hasher, comision_repo)

        with pytest.raises(PasswordDemasiadoCorta):
            await use_case.execute(
                "Ana", "ana.estudiante@fiuner.edu.ar", "abc123", comision.id
            )

        assert len(repo.usuarios) == 0
