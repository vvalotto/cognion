"""Puerto de broadcast en tiempo real por sesión (`US-6.1.1`).

Abstrae la publicación de mensajes hacia los participantes conectados de una sesión en vivo
(`BC-actividad-evaluativa-modelo.md` §16) sin que `use_cases/` conozca WebSockets ni ningún
detalle de `frameworks/` — mismo criterio que `NotificacionPort`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class CanalTiempoRealPort(ABC):
    """Publica mensajes a todos los conectados al canal de una sesión en vivo."""

    @abstractmethod
    async def publicar(self, sesion_id: UUID, mensaje: dict[str, Any]) -> None:
        """Entrega `mensaje` a todas las conexiones activas suscriptas a `sesion_id`.

        Sin destinatarios conectados, es un no-op. Nunca lanza una excepción por una conexión
        individual ya cerrada — la desconexión de un cliente no debe afectar la entrega a los
        demás.
        """
