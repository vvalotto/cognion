from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import JWTInvalido
from src.identidad.entities.invitacion import Invitacion
from src.identidad.entities.jwt import JWT, JWTPayload
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.entities.ports.invitacion_repository_port import InvitacionRepositoryPort
from src.identidad.entities.ports.jwt_issuer_port import JWTIssuerPort
from src.identidad.entities.ports.notificador_port import NotificadorPort
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import TipoPerfil, Usuario


class FakeUsuarioRepository(UsuarioRepositoryPort):
    def __init__(self) -> None:
        self.usuarios: dict[UUID, Usuario] = {}

    async def existe_email(self, email: str) -> bool:
        return any(u.email == email for u in self.usuarios.values())

    async def guardar(self, usuario: Usuario) -> None:
        self.usuarios[usuario.id] = usuario

    async def obtener_por_id(self, usuario_id: UUID) -> Usuario | None:
        return self.usuarios.get(usuario_id)

    async def obtener_por_email(self, email: str) -> Usuario | None:
        return next((u for u in self.usuarios.values() if u.email == email), None)


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


class FakeJWTIssuer(JWTIssuerPort):
    def __init__(self) -> None:
        self.emitidos: list[tuple[UUID, TipoPerfil]] = []
        self.payload_a_devolver: JWTPayload | None = None
        self.excepcion_a_levantar: Exception | None = None

    def emitir(self, usuario_id: UUID, rol: TipoPerfil) -> JWT:
        self.emitidos.append((usuario_id, rol))
        return JWT(
            token=f"fake-token:{usuario_id}:{rol.value}",
            rol=rol,
            expira_en=datetime.now(UTC) + timedelta(minutes=60),
        )

    def verificar(self, token: str) -> JWTPayload:
        if self.excepcion_a_levantar is not None:
            raise self.excepcion_a_levantar
        if self.payload_a_devolver is not None:
            return self.payload_a_devolver
        raise JWTInvalido()
