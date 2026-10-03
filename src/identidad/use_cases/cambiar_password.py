"""Caso de uso: un Usuario autenticado cambia su propia contraseña."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from src.identidad.entities.errors import (
    PasswordActualIncorrecta,
    UsuarioNoExiste,
)
from src.identidad.entities.eventos import CuentaBloqueada, PasswordCambiada
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.politica_bloqueo import (
    es_ultimo_administrador_operativo,
    rechazar_si_bloqueada,
)


class CambiarPasswordUseCase:
    """Verifica la contraseña actual y fija la nueva sobre la propia cuenta (RF-19).

    Lleva un contador de intentos fallidos independiente del de login
    (`intentos_fallidos_password`) y bloquea la cuenta al 3er fallo consecutivo (INV-ID-10,
    `US-2.2.1`).
    """

    def __init__(
        self,
        usuario_repositorio: UsuarioRepositoryPort,
        hasher: PasswordHasherPort,
        duracion_bloqueo_temporal: timedelta = timedelta(minutes=15),
    ) -> None:
        """Recibe el repositorio, el hasher y la duración del bloqueo temporal (INV-ID-21)."""
        self._duracion_bloqueo_temporal = duracion_bloqueo_temporal
        self._usuario_repositorio = usuario_repositorio
        self._hasher = hasher

    async def execute(
        self, usuario_id: UUID, password_actual: str, password_nueva: str
    ) -> PasswordCambiada:
        """Cambia la contraseña de `usuario_id` si `password_actual` verifica.

        Lanza `UsuarioNoExiste` si la cuenta no existe, `CuentaBloqueadaError` sin verificar
        nada si ya está bloqueada, `PasswordActualIncorrecta` si `password_actual` no
        verifica (con `intentos_restantes` siempre fijado, y `evento_cuenta_bloqueada` si
        este fallo llega al 3er consecutivo) y `PasswordDemasiadoCorta` si `password_nueva`
        no cumple INV-ID-11.
        """
        usuario = await self._usuario_repositorio.obtener_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNoExiste(usuario_id)

        ahora = datetime.now(UTC)
        await rechazar_si_bloqueada(self._usuario_repositorio, usuario, ahora)

        if not self._hasher.verificar(password_actual, usuario.password_hash):
            alcanzo_umbral = usuario.registrar_fallo_cambio_password()
            exc = PasswordActualIncorrecta()
            exc.intentos_restantes = usuario.intentos_restantes_cambio_password()
            if alcanzo_umbral:
                es_ultimo = await es_ultimo_administrador_operativo(
                    self._usuario_repositorio, usuario
                )
                usuario.bloquear_por_intentos_fallidos(
                    es_ultimo, ahora, self._duracion_bloqueo_temporal
                )
                exc.evento_cuenta_bloqueada = CuentaBloqueada(usuario_id=usuario.id)
            await self._usuario_repositorio.actualizar(usuario)
            raise exc

        Usuario.validar_password_nueva(password_nueva)

        password_hash = self._hasher.hash(password_nueva)
        usuario.cambiar_password(password_hash)
        await self._usuario_repositorio.actualizar(usuario)

        return PasswordCambiada(usuario_id=usuario.id)
