"""Caso de uso: un Usuario autenticado cambia su propia contraseña."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.errors import (
    CuentaBloqueadaError,
    PasswordActualIncorrecta,
    UsuarioNoExiste,
)
from src.identidad.entities.eventos import CuentaBloqueada, PasswordCambiada
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Usuario


class CambiarPasswordUseCase:
    """Verifica la contraseña actual y fija la nueva sobre la propia cuenta (RF-19).

    Lleva un contador de intentos fallidos independiente del de login
    (`intentos_fallidos_password`) y bloquea la cuenta al 3er fallo consecutivo (INV-ID-10,
    `US-2.2.1`).
    """

    def __init__(
        self, usuario_repositorio: UsuarioRepositoryPort, hasher: PasswordHasherPort
    ) -> None:
        """Recibe el repositorio de usuarios y el hasher de contraseñas a usar."""
        self._usuario_repositorio = usuario_repositorio
        self._hasher = hasher

    async def execute(
        self, usuario_id: UUID, password_actual: str, password_nueva: str
    ) -> PasswordCambiada:
        """Cambia la contraseña de `usuario_id` si `password_actual` verifica.

        Lanza `UsuarioNoExiste` si la cuenta no existe, `CuentaBloqueadaError` sin verificar
        nada si ya está bloqueada, `PasswordActualIncorrecta` si `password_actual` no
        verifica (con `evento_cuenta_bloqueada` si este fallo llega al 3er consecutivo) y
        `PasswordDemasiadoCorta` si `password_nueva` no cumple INV-ID-11.
        """
        usuario = await self._usuario_repositorio.obtener_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNoExiste(usuario_id)

        if usuario.bloqueada:
            raise CuentaBloqueadaError(usuario.id)

        if not self._hasher.verificar(password_actual, usuario.password_hash):
            bloqueada_ahora = usuario.registrar_fallo_cambio_password()
            exc = PasswordActualIncorrecta()
            if bloqueada_ahora:
                exc.evento_cuenta_bloqueada = CuentaBloqueada(usuario_id=usuario.id)
            await self._usuario_repositorio.actualizar(usuario)
            raise exc

        Usuario.validar_password_nueva(password_nueva)

        password_hash = self._hasher.hash(password_nueva)
        usuario.cambiar_password(password_hash)
        await self._usuario_repositorio.actualizar(usuario)

        return PasswordCambiada(usuario_id=usuario.id)
