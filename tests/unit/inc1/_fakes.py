from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.invitacion import Invitacion
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.entities.ports.invitacion_repository_port import InvitacionRepositoryPort
from src.identidad.entities.ports.notificador_port import NotificadorPort
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Usuario


class FakeUsuarioRepository(UsuarioRepositoryPort):
    def __init__(self) -> None:
        self.usuarios: dict[UUID, Usuario] = {}

    async def existe_email(self, email: str) -> bool:
        return any(u.email == email for u in self.usuarios.values())

    async def guardar(self, usuario: Usuario) -> None:
        self.usuarios[usuario.id] = usuario

    async def obtener_por_id(self, usuario_id: UUID) -> Usuario | None:
        return self.usuarios.get(usuario_id)


class FakeComisionRepository(ComisionRepositoryPort):
    def __init__(self) -> None:
        self.comisiones: dict[UUID, Comision] = {}

    async def guardar(self, comision: Comision) -> None:
        self.comisiones[comision.id] = comision

    async def obtener_por_id(self, comision_id: UUID) -> Comision | None:
        return self.comisiones.get(comision_id)

    async def actualizar(self, comision: Comision) -> None:
        self.comisiones[comision.id] = comision


class FakePasswordHasher(PasswordHasherPort):
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verificar(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{password}"


class FakeInvitacionRepository(InvitacionRepositoryPort):
    def __init__(self) -> None:
        self.invitaciones: dict[UUID, Invitacion] = {}

    async def guardar(self, invitacion: Invitacion) -> None:
        self.invitaciones[invitacion.id] = invitacion

    async def obtener_por_token(self, token: str) -> Invitacion | None:
        return next((i for i in self.invitaciones.values() if i.token == token), None)

    async def actualizar(self, invitacion: Invitacion) -> None:
        self.invitaciones[invitacion.id] = invitacion


class FakeNotificador(NotificadorPort):
    def __init__(self) -> None:
        self.enviados: list[tuple[str, str]] = []

    async def enviar_invitacion(self, email_destinatario: str, token: str) -> None:
        self.enviados.append((email_destinatario, token))
