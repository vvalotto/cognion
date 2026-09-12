"""Adaptador SMTP propio del BC Notificaciones (`US-5.1.1`).

Mismo patrón que `src/identidad/frameworks/smtp/notificador_smtp.py` (`ADR-012`): `smtplib`
estándar envuelto en `asyncio.to_thread`, sin sumar `aiosmtplib` como dependencia nueva —
decidido con Víctor en la spec de esta US. Los dos adaptadores quedan separados por BC (mismo
criterio de duplicación consciente de `ADR-012`), pero comparten técnica y las mismas
variables de entorno `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`/`SMTP_FROM` de
`src/settings.py`, que ya eran genéricas.
"""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from src.notificaciones.entities.ports.canal_envio_port import CanalEnvioPort
from src.settings import settings


class SmtpCanalEnvio(CanalEnvioPort):
    """Envía notificaciones por email vía SMTP usando la configuración de `settings`."""

    async def enviar(self, destinatario_email: str, asunto: str, cuerpo: str) -> None:
        """Arma y envía el mensaje SMTP en un thread aparte (`smtplib` es bloqueante)."""
        await asyncio.to_thread(self._enviar_sync, destinatario_email, asunto, cuerpo)

    @staticmethod
    def _enviar_sync(destinatario_email: str, asunto: str, cuerpo: str) -> None:
        """Arma y envía el mensaje SMTP de forma bloqueante (corre en un thread aparte)."""
        mensaje = EmailMessage()
        mensaje["Subject"] = asunto
        mensaje["From"] = settings.smtp_from
        mensaje["To"] = destinatario_email
        mensaje.set_content(cuerpo)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as servidor:
            if settings.smtp_user:
                servidor.starttls()
                servidor.login(settings.smtp_user, settings.smtp_password)
            servidor.send_message(mensaje)
