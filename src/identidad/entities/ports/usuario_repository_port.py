from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.identidad.entities.usuario import Usuario


class UsuarioRepositoryPort(ABC):
    @abstractmethod
    async def existe_email(self, email: str) -> bool: ...

    @abstractmethod
    async def guardar(self, usuario: Usuario) -> None: ...

    @abstractmethod
    async def obtener_por_id(self, usuario_id: UUID) -> Usuario | None: ...
