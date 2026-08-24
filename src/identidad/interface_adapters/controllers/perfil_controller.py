"""Controller de la API para acciones self-service sobre la propia cuenta (RF-19)."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.eventos import PasswordCambiada
from src.identidad.use_cases.cambiar_password import CambiarPasswordUseCase


class PerfilController:
    """Adapta requests HTTP a los casos de uso self-service sobre la propia cuenta."""

    def __init__(self, cambiar_password: CambiarPasswordUseCase) -> None:
        """Recibe el caso de uso de cambio de contraseña a usar."""
        self._cambiar_password = cambiar_password

    async def cambiar_password(
        self, usuario_id: UUID, password_actual: str, password_nueva: str
    ) -> PasswordCambiada:
        """Delega el cambio de la propia contraseña en el caso de uso correspondiente."""
        return await self._cambiar_password.execute(usuario_id, password_actual, password_nueva)
