"""Controller de la API para la recuperación de contraseña por autoservicio."""

from __future__ import annotations

from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.confirmar_nueva_password import ConfirmarNuevaPasswordUseCase
from src.identidad.use_cases.solicitar_recuperacion_password import (
    SolicitarRecuperacionPasswordUseCase,
)


class RecuperacionPasswordController:
    """Adapta requests HTTP a los casos de uso de recuperación de contraseña."""

    def __init__(
        self,
        solicitar_recuperacion: SolicitarRecuperacionPasswordUseCase,
        confirmar_nueva_password: ConfirmarNuevaPasswordUseCase,
    ) -> None:
        """Recibe los casos de uso de solicitud y de confirmación de recuperación."""
        self._solicitar_recuperacion = solicitar_recuperacion
        self._confirmar_nueva_password = confirmar_nueva_password

    async def solicitar(self, email: str) -> None:
        """Delega la solicitud de recuperación en el caso de uso correspondiente."""
        await self._solicitar_recuperacion.execute(email)

    async def confirmar(self, token: str, password_nueva: str) -> Usuario:
        """Delega el canje del token por una contraseña nueva en el caso de uso correspondiente."""
        usuario, _evento = await self._confirmar_nueva_password.execute(token, password_nueva)
        return usuario
