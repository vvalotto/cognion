"""Puerto de persistencia de `Usuario`, implementado en interface_adapters/frameworks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.identidad.entities.usuario import Usuario


class UsuarioRepositoryPort(ABC):
    """Operaciones de persistencia requeridas sobre `Usuario`."""

    @abstractmethod
    async def existe_email(self, email: str) -> bool:
        """Indica si ya hay un usuario registrado con ese email."""
        ...

    @abstractmethod
    async def guardar(self, usuario: Usuario) -> None:
        """Persiste un usuario nuevo."""
        ...

    @abstractmethod
    async def obtener_por_id(self, usuario_id: UUID) -> Usuario | None:
        """Busca un usuario por id, o `None` si no existe."""
        ...
