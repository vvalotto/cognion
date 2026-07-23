"""Puerto de persistencia de `Invitacion`, implementado en interface_adapters/frameworks."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.identidad.entities.invitacion import Invitacion


class InvitacionRepositoryPort(ABC):
    """Operaciones de persistencia requeridas sobre `Invitacion`."""

    @abstractmethod
    async def guardar(self, invitacion: Invitacion) -> None:
        """Guarda una invitación nueva."""
