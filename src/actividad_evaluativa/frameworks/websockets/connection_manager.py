"""`ConnectionManager` — registro en memoria de conexiones WebSocket por sesión (`US-6.1.1`).

Un `dict[UUID, set[WebSocket]]` de un solo proceso, sin tabla de outbox propia — válido a la
escala real del proyecto (30-60 conexiones concurrentes por sesión,
`BC-actividad-evaluativa-modelo.md` §16), mismo criterio de "no sobre-diseñar para el volumen
real" ya aplicado en `VerificadorDeVencimientos` (§6b).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Registra conexiones WebSocket por `sesion_id` y transmite mensajes a cada canal."""

    def __init__(self) -> None:
        """Arranca sin ninguna conexión registrada."""
        self._conexiones: dict[UUID, set[WebSocket]] = {}

    async def conectar(self, sesion_id: UUID, websocket: WebSocket) -> None:
        """Acepta el handshake y registra `websocket` bajo el canal de `sesion_id`."""
        await websocket.accept()
        self._conexiones.setdefault(sesion_id, set()).add(websocket)

    def desconectar(self, sesion_id: UUID, websocket: WebSocket) -> None:
        """Quita `websocket` del canal de `sesion_id`, si estaba registrada.

        Silencioso ante una conexión que ya no está registrada — la desconexión nunca debe
        propagar una excepción hacia el llamador.
        """
        conexiones = self._conexiones.get(sesion_id)
        if conexiones is None:
            return
        conexiones.discard(websocket)
        if not conexiones:
            del self._conexiones[sesion_id]

    async def enviar_a_sesion(self, sesion_id: UUID, mensaje: dict[str, Any]) -> None:
        """Envía `mensaje` (JSON) a todas las conexiones activas del canal de `sesion_id`.

        Una conexión que falla al enviar (ya cerrada del lado del cliente, pero todavía no
        desregistrada) se remueve y se ignora — nunca interrumpe el envío a las demás.
        """
        conexiones = list(self._conexiones.get(sesion_id, ()))
        for websocket in conexiones:
            try:
                await websocket.send_json(mensaje)
            except Exception:  # noqa: BLE001 — cualquier falla de envío es una desconexión
                logger.info("Conexión inactiva detectada al publicar en sesión %s", sesion_id)
                self.desconectar(sesion_id, websocket)
