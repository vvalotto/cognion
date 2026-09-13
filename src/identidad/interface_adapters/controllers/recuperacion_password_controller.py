"""Controller de la API para la solicitud de recuperación de contraseña."""

from __future__ import annotations

from src.identidad.use_cases.solicitar_recuperacion_password import (
    SolicitarRecuperacionPasswordUseCase,
)


class RecuperacionPasswordController:
    """Adapta requests HTTP al caso de uso de solicitud de recuperación de contraseña."""

    def __init__(self, solicitar_recuperacion: SolicitarRecuperacionPasswordUseCase) -> None:
        """Recibe el caso de uso de solicitud de recuperación."""
        self._solicitar_recuperacion = solicitar_recuperacion

    async def solicitar(self, email: str) -> None:
        """Delega la solicitud de recuperación en el caso de uso correspondiente."""
        await self._solicitar_recuperacion.execute(email)
