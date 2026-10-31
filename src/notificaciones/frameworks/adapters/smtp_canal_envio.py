"""Adaptador SMTP del BC Notificaciones (`US-5.1.1`, `US-8.1.7`).

Delega el envío en `src/shared/frameworks/smtp.py`, que resuelve la cuenta de la materia (o la
global `SMTP_*`) y concentra el código `smtplib` antes duplicado con el de Identidad (`ADR-023`).
"""

from __future__ import annotations

from uuid import UUID

from src.notificaciones.entities.ports.canal_envio_port import CanalEnvioPort
from src.shared.frameworks.smtp import enviar_email


class SmtpCanalEnvio(CanalEnvioPort):
    """Envía notificaciones por email vía SMTP, desde la cuenta de la materia o la global."""

    async def enviar(
        self,
        destinatario_email: str,
        asunto: str,
        cuerpo: str,
        materia_id: UUID | None = None,
    ) -> None:
        """Envía el mensaje con la cuenta resuelta para `materia_id` (`ADR-023`)."""
        await enviar_email(materia_id, destinatario_email, asunto, cuerpo)
