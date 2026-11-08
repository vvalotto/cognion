"""Puerto de persistencia de `Invitacion`, implementado en interface_adapters/frameworks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.identidad.entities.invitacion import Invitacion


class InvitacionRepositoryPort(ABC):
    """Operaciones de persistencia requeridas sobre `Invitacion`."""

    @abstractmethod
    async def guardar(self, invitacion: Invitacion) -> None:
        """Guarda una invitación nueva."""

    @abstractmethod
    async def obtener_por_token(self, token: str) -> Invitacion | None:
        """Busca una invitación por token, o `None` si no existe."""

    @abstractmethod
    async def actualizar(self, invitacion: Invitacion) -> None:
        """Guarda cambios sobre una invitación existente."""

    @abstractmethod
    async def obtener_por_id(self, invitacion_id: UUID) -> Invitacion | None:
        """Busca una invitación por id, o `None` si no existe."""

    @abstractmethod
    async def obtener_grupal_vigente(self, comision_id: UUID, ahora: datetime) -> Invitacion | None:
        """Busca el link grupal vigente de la comisión (no revocado ni vencido), o `None`."""

    @abstractmethod
    async def obtener_ultima_grupal(self, comision_id: UUID) -> Invitacion | None:
        """Busca el último link grupal generado para la comisión, o `None` si nunca hubo."""

    @abstractmethod
    async def reemplazar(self, anterior: Invitacion | None, nueva: Invitacion) -> None:
        """Guarda `nueva` y los cambios de `anterior` (revocada) en una sola transacción."""

    @abstractmethod
    async def incrementar_usos(self, invitacion_id: UUID) -> None:
        """Suma un uso a la invitación con una sola sentencia atómica (sin leer y reescribir)."""
