"""Adaptador SMTP propio del BC Identidad para envío de invitaciones (`ADR-012`)."""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from src.identidad.entities.ports.notificador_port import NotificadorPort
from src.settings import settings


class SmtpNotificador(NotificadorPort):
    """Envía emails de invitación vía SMTP usando la configuración de `settings`."""

    async def enviar_invitacion(self, email_destinatario: str, token: str) -> None:
        """Arma y envía el email con el link de invitación al destinatario indicado."""
        await asyncio.to_thread(self._enviar_sync, email_destinatario, token)

    @staticmethod
    def _enviar_sync(email_destinatario: str, token: str) -> None:
        """Arma y envía el mensaje SMTP de forma bloqueante (corre en un thread aparte)."""
        mensaje = EmailMessage()
        mensaje["Subject"] = "Invitación a Cognión"
        mensaje["From"] = settings.smtp_from
        mensaje["To"] = email_destinatario
        mensaje.set_content(
            "Fuiste invitado a registrarte en Cognión.\n"
            f"Token de invitación: {token}\n"
            "Válido por 7 días desde su generación."
        )

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as servidor:
            if settings.smtp_user:
                servidor.starttls()
                servidor.login(settings.smtp_user, settings.smtp_password)
            servidor.send_message(mensaje)
