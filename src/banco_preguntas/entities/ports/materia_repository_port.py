"""Puerto de persistencia de `Materia`, implementado en interface_adapters/frameworks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.banco_preguntas.entities.materia import Materia


class MateriaRepositoryPort(ABC):
    """Operaciones de persistencia requeridas sobre `Materia`."""

    @abstractmethod
    async def guardar(self, materia: Materia) -> None:
        """Guarda una materia nueva."""

    @abstractmethod
    async def actualizar(self, materia: Materia) -> None:
        """Guarda cambios sobre una materia existente (nombre y `activa`)."""

    @abstractmethod
    async def eliminar(self, materia_id: UUID) -> None:
        """Borra físicamente una materia sin preguntas ni comisiones asociadas."""

    @abstractmethod
    async def obtener_por_nombre(self, nombre: str) -> Materia | None:
        """Busca una materia por nombre, o `None` si no existe (INV-BP-00)."""

    @abstractmethod
    async def obtener_por_id(self, materia_id: UUID) -> Materia | None:
        """Busca una materia por id, o `None` si no existe."""

    @abstractmethod
    async def listar(self, incluir_inactivas: bool = False) -> list[Materia]:
        """Lista las materias activas; con `incluir_inactivas=True`, también las deshabilitadas."""
