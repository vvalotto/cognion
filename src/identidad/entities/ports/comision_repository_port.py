from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.identidad.entities.comision import Comision


class ComisionRepositoryPort(ABC):
    @abstractmethod
    async def guardar(self, comision: Comision) -> None: ...

    @abstractmethod
    async def obtener_por_id(self, comision_id: UUID) -> Comision | None: ...

    @abstractmethod
    async def actualizar(self, comision: Comision) -> None: ...
