"""Puerto de envío del email de recuperación de contraseña, dueño de BC Identidad (`US-ADJ-38`).

Puerto de disparo hacia BC Notificaciones — comunicación entre BCs solo por puertos definidos
en `entities/ports/` (`CLAUDE.md`), nunca por import directo. Primera vez que Identidad
depende de un puerto de Notificaciones (`BC-identidad-modelo.md` §13.2); se resuelve con el
mismo mecanismo ya ratificado en `ADR-006` para el sentido inverso (Actividad Evaluativa →
Notificaciones, `NotificacionPort`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class CanalRecuperacionPort(ABC):
    """Envía el email de recuperación de contraseña con el link/token correspondiente."""

    @abstractmethod
    async def enviar_recuperacion(self, email_destinatario: str, token: str) -> None:
        """Envía el link de recuperación (con `token`) al email indicado.

        No captura ni convierte excepciones — el manejo de fallos de envío ("loguear y
        continuar", mismo criterio que Notificaciones, `BL-009`) es responsabilidad del Use
        Case que invoca este puerto, no del adapter (mismo contrato que `CanalEnvioPort` de
        BC Notificaciones).
        """
