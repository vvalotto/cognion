"""Controller de la API para la autenticación de Usuarios."""

from __future__ import annotations

from src.identidad.entities.eventos import SesionIniciada
from src.identidad.entities.jwt import JWT
from src.identidad.use_cases.iniciar_sesion import IniciarSesionUseCase


class AuthController:
    """Adapta requests HTTP al caso de uso de autenticación."""

    def __init__(self, iniciar_sesion: IniciarSesionUseCase) -> None:
        """Recibe el caso de uso de inicio de sesión a usar."""
        self._iniciar_sesion = iniciar_sesion

    async def iniciar_sesion(self, email: str, password: str) -> tuple[JWT, SesionIniciada]:
        """Delega la autenticación en el caso de uso correspondiente."""
        return await self._iniciar_sesion.execute(email, password)
