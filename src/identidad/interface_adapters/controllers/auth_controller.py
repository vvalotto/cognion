"""Controller de la API para la autenticación de Usuarios."""

from __future__ import annotations

from src.identidad.interface_adapters.presenters.identidad_presenter import (
    LoginSalida,
    presentar_login,
)
from src.identidad.use_cases.iniciar_sesion import IniciarSesionUseCase


class AuthController:
    """Adapta requests HTTP al caso de uso de autenticación."""

    def __init__(self, iniciar_sesion: IniciarSesionUseCase) -> None:
        """Recibe el caso de uso de inicio de sesión a usar."""
        self._iniciar_sesion = iniciar_sesion

    async def iniciar_sesion(self, email: str, password: str) -> LoginSalida:
        """Delega la autenticación en el caso de uso correspondiente."""
        jwt, _evento = await self._iniciar_sesion.execute(email, password)
        return presentar_login(jwt)
