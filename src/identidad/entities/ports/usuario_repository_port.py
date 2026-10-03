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
        """Guarda un usuario nuevo."""
        ...

    @abstractmethod
    async def actualizar(self, usuario: Usuario) -> None:
        """Guarda cambios sobre un usuario existente (contraseña, bloqueo, contadores)."""
        ...

    @abstractmethod
    async def eliminar(self, usuario_id: UUID) -> None:
        """Borra físicamente un usuario sin datos asociados, junto con su fila de perfil."""
        ...

    @abstractmethod
    async def contar_administradores_operativos(self, excluyendo: UUID | None = None) -> int:
        """Cuenta los Administradores ni deshabilitados ni bloqueados (INV-ID-20).

        `excluyendo` omite a ese usuario del conteo (para saber si existe *otro* operativo).
        """
        ...

    @abstractmethod
    async def obtener_por_id(self, usuario_id: UUID) -> Usuario | None:
        """Busca un usuario por id, o `None` si no existe."""
        ...

    @abstractmethod
    async def obtener_por_email(self, email: str) -> Usuario | None:
        """Busca un usuario por email, o `None` si no existe."""
        ...
