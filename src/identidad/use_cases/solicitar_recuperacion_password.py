"""Caso de uso: solicitud de recuperación de contraseña por autoservicio."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from src.identidad.entities.ports.canal_recuperacion_port import CanalRecuperacionPort
from src.identidad.entities.ports.token_recuperacion_password_repository_port import (
    TokenRecuperacionPasswordRepositoryPort,
)
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.token_recuperacion_password import TokenRecuperacionPassword

logger = logging.getLogger(__name__)


class SolicitarRecuperacionPasswordUseCase:
    """Genera y envía un token de recuperación si `email` corresponde a una cuenta (RF nuevo).

    No expone al llamante si la cuenta existe o no (INV-ID-17) — `execute()` no retorna nada
    ni lanza excepciones por ausencia de cuenta: el router responde siempre el mismo mensaje
    genérico, sin importar el resultado interno.
    """

    def __init__(
        self,
        usuario_repositorio: UsuarioRepositoryPort,
        token_repositorio: TokenRecuperacionPasswordRepositoryPort,
        canal_recuperacion: CanalRecuperacionPort,
    ) -> None:
        """Recibe los repositorios de usuarios y tokens, y el canal de envío a usar."""
        self._usuario_repositorio = usuario_repositorio
        self._token_repositorio = token_repositorio
        self._canal_recuperacion = canal_recuperacion

    async def execute(self, email: str) -> None:
        """Genera un token nuevo y dispara el email si `email` corresponde a una cuenta.

        Si no existe ninguna cuenta con ese email, no hace nada (INV-ID-17). Si existe,
        invalida cualquier token activo previo del mismo usuario (INV-ID-12) antes de crear
        y persistir el nuevo, y envía el email vía `CanalRecuperacionPort`. Un fallo de envío
        se loguea y no bloquea la operación — el token queda creado igual (mismo criterio que
        `NotificarAperturaUseCase` de Notificaciones, `BL-009`).
        """
        usuario = await self._usuario_repositorio.obtener_por_email(email)
        if usuario is None:
            return

        ahora = datetime.now(UTC)
        await self._token_repositorio.invalidar_activos_de(usuario.id, ahora)

        token = TokenRecuperacionPassword.crear(usuario.id)
        await self._token_repositorio.guardar(token)

        try:
            await self._canal_recuperacion.enviar_recuperacion(usuario.email, token.token)
        except Exception:  # pylint: disable=broad-except
            logger.warning(
                "Fallo al enviar email de recuperación de contraseña a usuario %s",
                usuario.id,
                exc_info=True,
            )
