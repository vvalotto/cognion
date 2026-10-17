"""Envío de email por SMTP con la cuenta resuelta por materia (`ADR-023`, `US-8.1.7`).

Transversal a los BC que envían email (Notificaciones, Identidad): un único lugar donde se decide
desde qué cuenta sale cada mensaje y donde vive el código SMTP bloqueante (`ADR-017`).
"""

from __future__ import annotations

import asyncio
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from uuid import UUID

from src.settings import settings


@dataclass(frozen=True)
class CuentaSmtp:
    """Servidor, credenciales y remitente con los que sale un email."""

    host: str
    port: int
    user: str
    password: str
    remitente: str


def resolver_cuenta_smtp(materia_id: UUID | None) -> CuentaSmtp:
    """Devuelve la cuenta de la materia si tiene una propia; si no, la cuenta global `SMTP_*`.

    Lee `settings` en cada llamada (no en la importación) para respetar cambios de entorno y los
    ajustes que hacen los tests sobre el singleton.
    """
    cuenta_materia = (
        settings.smtp_cuentas_por_materia.get(materia_id) if materia_id is not None else None
    )
    if cuenta_materia is not None:
        return CuentaSmtp(
            host=cuenta_materia.host,
            port=cuenta_materia.port,
            user=cuenta_materia.user,
            password=cuenta_materia.password,
            remitente=cuenta_materia.remitente,
        )
    return CuentaSmtp(
        host=settings.smtp_host,
        port=settings.smtp_port,
        user=settings.smtp_user,
        password=settings.smtp_password,
        remitente=settings.smtp_from,
    )


def _enviar_sync(cuenta: CuentaSmtp, destinatario: str, asunto: str, cuerpo: str) -> None:
    """Arma y envía el mensaje de forma bloqueante (corre en un thread aparte)."""
    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = cuenta.remitente
    mensaje["To"] = destinatario
    mensaje.set_content(cuerpo)

    with smtplib.SMTP(cuenta.host, cuenta.port) as servidor:
        if cuenta.user:
            servidor.starttls()
            servidor.login(cuenta.user, cuenta.password)
        servidor.send_message(mensaje)


async def enviar_email(
    materia_id: UUID | None, destinatario: str, asunto: str, cuerpo: str
) -> None:
    """Envía un email desde la cuenta de `materia_id` (o la global) sin bloquear el event loop."""
    await asyncio.to_thread(
        _enviar_sync, resolver_cuenta_smtp(materia_id), destinatario, asunto, cuerpo
    )
