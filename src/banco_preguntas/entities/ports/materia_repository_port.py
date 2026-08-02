"""Puerto de persistencia de `Materia`, implementado en interface_adapters/frameworks."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.banco_preguntas.entities.materia import Materia


class MateriaRepositoryPort(ABC):
    """Operaciones de persistencia requeridas sobre `Materia`."""

    @abstractmethod
    async def guardar(self, materia: Materia) -> None:
        """Guarda una materia nueva."""

    @abstractmethod
    async def obtener_por_nombre(self, nombre: str) -> Materia | None:
        """Busca una materia por nombre, o `None` si no existe (INV-BP-00)."""
