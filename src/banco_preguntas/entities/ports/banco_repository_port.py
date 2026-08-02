"""Puerto de persistencia de `Banco`, implementado en interface_adapters/frameworks."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.banco_preguntas.entities.banco import Banco


class BancoRepositoryPort(ABC):
    """Operaciones de persistencia requeridas sobre `Banco`."""

    @abstractmethod
    async def guardar(self, banco: Banco) -> None:
        """Guarda un banco nuevo."""
