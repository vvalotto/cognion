"""Adaptador de `CanalRecuperacionPort` — llamada in-process a BC Notificaciones (`US-ADJ-38`).

Único punto de Identidad que importa `src.notificaciones` — mismo criterio de acoplamiento
consciente (`ADR-006`) que los demás adapters `*_in_process.py` cruzados del proyecto
(`notificacion_port_in_process.py` de Actividad Evaluativa hacia Notificaciones,
`materia_port_in_process.py`/`evaluacion_consulta_port_in_process.py` de Identidad hacia otros
BCs). Vive en `frameworks/`, nunca en `entities/` ni `use_cases/`.

A diferencia de `NotificacionPortInProcess` (que orquesta `NotificarAperturaUseCase`/
`NotificarCierreUseCase` porque esos necesitan resolver un roster vía `ComisionConsultaPort`),
acá el destinatario ya lo tiene Identidad — se invoca `CanalEnvioPort`/`SmtpCanalEnvio`
directo, sin pasar por un Use Case de Notificaciones.
"""

from __future__ import annotations

from src.identidad.entities.ports.canal_recuperacion_port import CanalRecuperacionPort
from src.notificaciones.frameworks.adapters.smtp_canal_envio import SmtpCanalEnvio
from src.settings import settings


class CanalRecuperacionPortInProcess(CanalRecuperacionPort):
    """Implementa `CanalRecuperacionPort` invocando `SmtpCanalEnvio` de Notificaciones."""

    def __init__(self) -> None:
        """Arma internamente el canal de envío de Notificaciones a reusar."""
        self._canal_envio = SmtpCanalEnvio()

    async def enviar_recuperacion(self, email_destinatario: str, token: str) -> None:
        """Compone y envía el email de recuperación.

        No captura excepciones (ver `CanalRecuperacionPort.enviar_recuperacion`) — el manejo
        de un fallo de envío es responsabilidad del Use Case que invoca este puerto.
        """
        link = f"{settings.frontend_url}/recuperar-password/{token}"
        asunto = "Recuperar tu contraseña"
        cuerpo = (
            "Recibimos una solicitud para recuperar el acceso a tu cuenta.\n\n"
            f"Ingresá a este link para definir una contraseña nueva: {link}\n\n"
            "Este link vence en 1 hora. Si no solicitaste este cambio, podés ignorar este "
            "email."
        )
        await self._canal_envio.enviar(email_destinatario, asunto, cuerpo)
