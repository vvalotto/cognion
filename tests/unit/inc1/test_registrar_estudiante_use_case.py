import uuid
from datetime import UTC, datetime, timedelta

import pytest

from src.identidad.entities.errors import (
    EmailYaRegistrado,
    InvitacionInvalida,
    InvitacionVencida,
    InvitacionYaUsada,
)
from src.identidad.entities.eventos import InvitacionAceptada, UsuarioRegistrado
from src.identidad.entities.invitacion import Invitacion
from src.identidad.entities.usuario import Estudiante, Usuario
from src.identidad.use_cases.registrar_estudiante import RegistrarEstudianteUseCase
from tests.unit.inc1._fakes import (
    FakeInvitacionRepository,
    FakePasswordHasher,
    FakeUsuarioRepository,
)


class TestRegistrarEstudianteUseCase:
    async def test_registra_estudiante_con_invitacion_vigente(self):
        invitacion_repo = FakeInvitacionRepository()
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        comision_id = uuid.uuid4()
        invitacion = Invitacion.crear(comision_id, uuid.uuid4())
        await invitacion_repo.guardar(invitacion)

        use_case = RegistrarEstudianteUseCase(invitacion_repo, usuario_repo, hasher)
        usuario, evento_invitacion, evento_usuario = await use_case.execute(
            invitacion.token, "Nico", "nico@fiuner.edu.ar", "password123"
        )

        assert isinstance(usuario.perfil, Estudiante)
        assert usuario.perfil.comision_id == comision_id
        assert usuario.password_hash == hasher.hash("password123")
        assert usuario.id in usuario_repo.usuarios

        assert isinstance(evento_invitacion, InvitacionAceptada)
        assert evento_invitacion.usuario_id == usuario.id
        assert evento_invitacion.comision_id == comision_id
        assert isinstance(evento_usuario, UsuarioRegistrado)
        assert evento_usuario.usuario_id == usuario.id
        assert evento_usuario.comision_id == comision_id

    async def test_marca_la_invitacion_como_usada(self):
        invitacion_repo = FakeInvitacionRepository()
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())
        await invitacion_repo.guardar(invitacion)

        use_case = RegistrarEstudianteUseCase(invitacion_repo, usuario_repo, hasher)
        await use_case.execute(invitacion.token, "Nico", "nico@fiuner.edu.ar", "password123")

        assert invitacion_repo.invitaciones[invitacion.id].usada_en is not None

    async def test_rechaza_email_ya_registrado_sin_consumir_la_invitacion(self):
        invitacion_repo = FakeInvitacionRepository()
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())
        await invitacion_repo.guardar(invitacion)
        usuario_repo.usuarios[uuid.uuid4()] = _usuario_con_email("nico@fiuner.edu.ar")

        use_case = RegistrarEstudianteUseCase(invitacion_repo, usuario_repo, hasher)

        with pytest.raises(EmailYaRegistrado):
            await use_case.execute(invitacion.token, "Nico", "nico@fiuner.edu.ar", "password123")

        assert invitacion_repo.invitaciones[invitacion.id].usada_en is None

    async def test_rechaza_token_inexistente(self):
        invitacion_repo = FakeInvitacionRepository()
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()

        use_case = RegistrarEstudianteUseCase(invitacion_repo, usuario_repo, hasher)

        with pytest.raises(InvitacionInvalida):
            await use_case.execute("token-inexistente", "Nico", "nico@fiuner.edu.ar", "password123")

        assert usuario_repo.usuarios == {}

    async def test_rechaza_invitacion_vencida(self):
        invitacion_repo = FakeInvitacionRepository()
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())
        invitacion.expira_en = datetime.now(UTC) - timedelta(days=1)
        await invitacion_repo.guardar(invitacion)

        use_case = RegistrarEstudianteUseCase(invitacion_repo, usuario_repo, hasher)

        with pytest.raises(InvitacionVencida):
            await use_case.execute(invitacion.token, "Nico", "nico@fiuner.edu.ar", "password123")

        assert usuario_repo.usuarios == {}

    async def test_rechaza_invitacion_ya_usada(self):
        invitacion_repo = FakeInvitacionRepository()
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())
        invitacion.aceptar(datetime.now(UTC))
        await invitacion_repo.guardar(invitacion)

        use_case = RegistrarEstudianteUseCase(invitacion_repo, usuario_repo, hasher)

        with pytest.raises(InvitacionYaUsada):
            await use_case.execute(invitacion.token, "Nico", "nico@fiuner.edu.ar", "password123")

        assert usuario_repo.usuarios == {}


def _usuario_con_email(email: str) -> Usuario:
    return Usuario.crear_estudiante("Otro", email, "hash", uuid.uuid4())
