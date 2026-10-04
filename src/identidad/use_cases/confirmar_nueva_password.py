"""Caso de uso: confirmación de una contraseña nueva con token de recuperación."""

from __future__ import annotations

from datetime import UTC, datetime

from src.identidad.entities.errors import TokenRecuperacionInvalido, UsuarioNoExiste
from src.identidad.entities.eventos import CuentaDesbloqueada, PasswordRecuperada
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.token_recuperacion_password_repository_port import (
    TokenRecuperacionPasswordRepositoryPort,
)
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.token_recuperacion_password import TokenRecuperacionPassword
from src.identidad.entities.usuario import Usuario


class ConfirmarNuevaPasswordUseCase:
    """Canjea un `TokenRecuperacionPassword` vigente por una contraseña nueva (`US-ADJ-39`)."""

    def __init__(
        self,
        usuario_repositorio: UsuarioRepositoryPort,
        token_repositorio: TokenRecuperacionPasswordRepositoryPort,
        hasher: PasswordHasherPort,
    ) -> None:
        """Recibe los repositorios de usuarios y tokens, y el hasher a usar."""
        self._usuario_repositorio = usuario_repositorio
        self._token_repositorio = token_repositorio
        self._hasher = hasher

    async def execute(
        self, token: str, password_nueva: str
    ) -> tuple[Usuario, PasswordRecuperada, CuentaDesbloqueada | None]:
        """Actualiza `Usuario.password_hash`, desbloquea la cuenta y marca el token como usado.

        Lanza `TokenRecuperacionInvalido` si el token no corresponde a ninguno existente,
        `TokenRecuperacionYaUsado`/`TokenRecuperacionVencido` si ya no está vigente
        (INV-ID-13), o `PasswordDemasiadoCorta`/`PasswordSinComplejidadSuficiente` si
        `password_nueva` no cumple INV-ID-11 ampliada. Desbloquea la cuenta y resetea sus
        contadores (`US-ADJ-62`); `CuentaDesbloqueada` solo se emite si estaba bloqueada.
        No reactiva una cuenta `deshabilitada`.
        """
        token_recuperacion = await self._buscar_token_vigente(token)

        usuario = await self._usuario_repositorio.obtener_por_id(token_recuperacion.usuario_id)
        if usuario is None:
            raise UsuarioNoExiste(token_recuperacion.usuario_id)

        Usuario.validar_password_nueva(password_nueva)

        password_hash = self._hasher.hash(password_nueva)
        estaba_bloqueada = usuario.recuperar_password(password_hash)
        await self._usuario_repositorio.actualizar(usuario)

        ahora = datetime.now(UTC)
        token_recuperacion.invalidar(ahora)
        await self._token_repositorio.actualizar(token_recuperacion)

        evento = PasswordRecuperada(usuario_id=usuario.id)
        evento_desbloqueo = CuentaDesbloqueada(usuario_id=usuario.id) if estaba_bloqueada else None
        return usuario, evento, evento_desbloqueo

    async def _buscar_token_vigente(self, token: str) -> TokenRecuperacionPassword:
        """Busca el token por valor y valida su vigencia sin consumirlo.

        Lanza `TokenRecuperacionInvalido` si el token no corresponde a ninguno existente;
        delega en `TokenRecuperacionPassword.verificar_vigente` la distinción entre vencido y
        ya usado.
        """
        token_recuperacion = await self._token_repositorio.obtener_por_token(token)
        if token_recuperacion is None:
            raise TokenRecuperacionInvalido(token)
        token_recuperacion.verificar_vigente(datetime.now(UTC))
        return token_recuperacion
