"""Caso de uso: reseteo de contraseña de una cuenta, con desbloqueo si corresponde."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.errors import UsuarioNoExiste
from src.identidad.entities.eventos import CuentaDesbloqueada, PasswordReseteada
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Usuario


class ResetearPasswordUseCase:
    """Fija una contraseña nueva para una cuenta y la desbloquea si estaba bloqueada (RF-03)."""

    def __init__(
        self, usuario_repositorio: UsuarioRepositoryPort, hasher: PasswordHasherPort
    ) -> None:
        """Recibe el repositorio de usuarios y el hasher de contraseñas a usar."""
        self._usuario_repositorio = usuario_repositorio
        self._hasher = hasher

    async def execute(
        self, usuario_id: UUID, password_nueva: str, administrador_id: UUID
    ) -> tuple[Usuario, PasswordReseteada, CuentaDesbloqueada | None]:
        """Resetea la contraseña de `usuario_id` y devuelve el usuario junto a los eventos.

        Lanza `UsuarioNoExiste` si la cuenta no existe, `PasswordDemasiadoCorta` si
        `password_nueva` no cumple INV-ID-11. `CuentaDesbloqueada` solo se emite si la cuenta
        estaba bloqueada antes del reseteo.
        """
        usuario = await self._usuario_repositorio.obtener_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNoExiste(usuario_id)

        Usuario.validar_password_nueva(password_nueva)

        password_hash = self._hasher.hash(password_nueva)
        estaba_bloqueada = usuario.resetear_password(password_hash)
        await self._usuario_repositorio.actualizar(usuario)

        evento_password = PasswordReseteada(
            usuario_id=usuario.id, administrador_id=administrador_id
        )
        evento_desbloqueo = CuentaDesbloqueada(usuario_id=usuario.id) if estaba_bloqueada else None
        return usuario, evento_password, evento_desbloqueo
