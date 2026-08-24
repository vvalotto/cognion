"""Puerto de envío de notificaciones por email del BC Identidad (`ADR-012`)."""

from __future__ import annotations

from abc import ABC, abstractmethod


class NotificadorPort(ABC):
    """Operaciones de envío de email requeridas por el BC Identidad."""

    @abstractmethod
    async def enviar_invitacion(self, email_destinatario: str, token: str) -> None:
        """Envía el link de invitación (con `token`) al email indicado."""
