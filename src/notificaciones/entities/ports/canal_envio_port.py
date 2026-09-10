"""Puerto de envío de notificaciones, abstracción del canal concreto (RF-14).

Vive en Notificaciones — RF-14 pide que el canal de notificación sea extensible a otros
medios en el futuro sin tocar el Use Case que lo invoca (`BC-notificaciones-modelo.md` §5).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class CanalEnvioPort(ABC):
    """Envía un mensaje de notificación por el canal concreto que implemente el adapter."""

    @abstractmethod
    async def enviar(self, destinatario_email: str, asunto: str, cuerpo: str) -> None:
        """Envía el mensaje al destinatario indicado.

        No captura ni convierte excepciones — el manejo de fallos de envío ("loguear y
        continuar", `BC-notificaciones-modelo.md` §6 decisión 4) es responsabilidad del Use
        Case que invoca este puerto, no del adapter.
        """
        ...
