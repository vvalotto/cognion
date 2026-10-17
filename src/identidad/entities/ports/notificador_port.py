"""Puerto de envío de notificaciones por email del BC Identidad (`ADR-012`)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class NotificadorPort(ABC):
    """Operaciones de envío de email requeridas por el BC Identidad."""

    @abstractmethod
    async def enviar_invitacion(
        self, email_destinatario: str, token: str, materia_id: UUID | None = None
    ) -> None:
        """Envía el link de invitación (con `token`) al email indicado.

        `materia_id` es la materia de la comisión, para usar la cuenta de envío de esa materia
        (`ADR-023`); `None` usa la cuenta global.
        """
