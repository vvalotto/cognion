"""Adaptador SMTP propio del BC Identidad para envío de invitaciones (`ADR-012`)."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.ports.notificador_port import NotificadorPort
from src.shared.frameworks.smtp import enviar_email


class SmtpNotificador(NotificadorPort):
    """Envía emails de invitación vía SMTP, desde la cuenta de la materia o la global."""

    async def enviar_invitacion(
        self, email_destinatario: str, token: str, materia_id: UUID | None = None
    ) -> None:
        """Arma y envía el email con el link de invitación al destinatario indicado."""
        cuerpo = (
            "Fuiste invitado a registrarte en Cognión.\n"
            f"Token de invitación: {token}\n"
            "Válido por 7 días desde su generación."
        )
        await enviar_email(materia_id, email_destinatario, "Invitación a Cognión", cuerpo)
