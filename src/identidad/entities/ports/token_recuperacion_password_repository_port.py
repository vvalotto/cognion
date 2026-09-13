"""Puerto de persistencia de `TokenRecuperacionPassword`, implementado en frameworks/."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.identidad.entities.token_recuperacion_password import TokenRecuperacionPassword


class TokenRecuperacionPasswordRepositoryPort(ABC):
    """Operaciones de persistencia requeridas sobre `TokenRecuperacionPassword`."""

    @abstractmethod
    async def guardar(self, token: TokenRecuperacionPassword) -> None:
        """Guarda un token nuevo."""

    @abstractmethod
    async def obtener_por_token(self, token: str) -> TokenRecuperacionPassword | None:
        """Busca un token de recuperación por su valor, o `None` si no existe."""

    @abstractmethod
    async def invalidar_activos_de(self, usuario_id: UUID, ahora: datetime) -> None:
        """Marca como usado (INV-ID-12) cualquier token sin usar de `usuario_id`.

        Actualización directa contra la tabla — no requiere traer los tokens afectados a
        memoria antes de invalidarlos.
        """

    @abstractmethod
    async def actualizar(self, token: TokenRecuperacionPassword) -> None:
        """Guarda cambios sobre un token existente (por ejemplo, tras un canje exitoso)."""
