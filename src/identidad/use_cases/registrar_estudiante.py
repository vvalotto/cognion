"""Caso de uso: registro de un Estudiante vía invitación."""

from __future__ import annotations

from datetime import UTC, datetime

from src.identidad.entities.errors import EmailYaRegistrado, InvitacionNoValida
from src.identidad.entities.eventos import InvitacionAceptada, UsuarioRegistrado
from src.identidad.entities.invitacion import Invitacion
from src.identidad.entities.ports.invitacion_repository_port import InvitacionRepositoryPort
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Usuario


class RegistrarEstudianteUseCase:
    """Registra un Estudiante que acepta una invitación vigente y lo asigna a su comisión."""

    def __init__(
        self,
        invitacion_repositorio: InvitacionRepositoryPort,
        usuario_repositorio: UsuarioRepositoryPort,
        hasher: PasswordHasherPort,
    ) -> None:
        """Recibe los repositorios de invitaciones y usuarios, y el hasher a usar."""
        self._invitacion_repositorio = invitacion_repositorio
        self._usuario_repositorio = usuario_repositorio
        self._hasher = hasher

    async def execute(
        self, token: str, nombre: str, email: str, password: str
    ) -> tuple[Usuario, InvitacionAceptada, UsuarioRegistrado]:
        """Crea el Usuario con perfil Estudiante y consume la invitación en la misma operación.

        Lanza `InvitacionNoValida` si el token no corresponde a ninguna invitación o ya no
        está vigente (INV-ID-01, INV-ID-03), y `EmailYaRegistrado` si el email ya está en uso
        (INV-ID-04). Ninguna invitación se marca como usada si el registro se rechaza.
        """
        invitacion = await self._buscar_invitacion_vigente(token)

        if await self._usuario_repositorio.existe_email(email):
            raise EmailYaRegistrado(email)

        password_hash = self._hasher.hash(password)
        usuario = Usuario.crear_estudiante(nombre, email, password_hash, invitacion.comision_id)
        await self._usuario_repositorio.guardar(usuario)

        invitacion.aceptar(datetime.now(UTC))
        await self._invitacion_repositorio.actualizar(invitacion)

        evento_invitacion = InvitacionAceptada(
            invitacion_id=invitacion.id, comision_id=invitacion.comision_id, usuario_id=usuario.id
        )
        evento_usuario = UsuarioRegistrado(
            usuario_id=usuario.id, email=usuario.email, comision_id=invitacion.comision_id
        )
        return usuario, evento_invitacion, evento_usuario

    async def _buscar_invitacion_vigente(self, token: str) -> Invitacion:
        """Busca la invitación por token y valida su vigencia sin consumirla."""
        invitacion = await self._invitacion_repositorio.obtener_por_token(token)
        if invitacion is None or not invitacion.es_vigente(datetime.now(UTC)):
            raise InvitacionNoValida(token)
        return invitacion
