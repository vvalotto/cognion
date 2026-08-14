"""Puerto de persistencia de `Banco`, implementado en interface_adapters/frameworks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.banco_preguntas.entities.banco import Banco


class BancoRepositoryPort(ABC):
    """Operaciones de persistencia requeridas sobre `Banco`."""

    @abstractmethod
    async def guardar(self, banco: Banco) -> None:
        """Guarda un banco nuevo."""

    @abstractmethod
    async def obtener_por_id(self, banco_id: UUID) -> Banco | None:
        """Busca un banco por id, o `None` si no existe."""

    @abstractmethod
    async def obtener_por_materia_id(self, materia_id: UUID) -> Banco | None:
        """Busca el banco de una materia, o `None` si no existe (1:1, INV-BP-01)."""
