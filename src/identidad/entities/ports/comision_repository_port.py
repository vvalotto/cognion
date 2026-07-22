"""Puerto de persistencia de `Comision`, implementado en interface_adapters/frameworks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.identidad.entities.comision import Comision


class ComisionRepositoryPort(ABC):
    """Operaciones de persistencia requeridas sobre `Comision`."""

    @abstractmethod
    async def guardar(self, comision: Comision) -> None:
        """Persiste una comisión nueva."""
        ...

    @abstractmethod
    async def obtener_por_id(self, comision_id: UUID) -> Comision | None:
        """Busca una comisión por id, o `None` si no existe."""
        ...

    @abstractmethod
    async def actualizar(self, comision: Comision) -> None:
        """Persiste cambios sobre una comisión existente."""
        ...
