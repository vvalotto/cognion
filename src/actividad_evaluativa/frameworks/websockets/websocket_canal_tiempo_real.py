"""Implementación de `CanalTiempoRealPort` sobre WebSockets (`US-6.1.1`)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.ports.canal_tiempo_real_port import CanalTiempoRealPort
from src.actividad_evaluativa.frameworks.websockets.connection_manager import ConnectionManager


class WebSocketCanalTiempoReal(CanalTiempoRealPort):
    """Publica por WebSocket delegando en un `ConnectionManager` compartido del proceso."""

    def __init__(self, connection_manager: ConnectionManager) -> None:
        """Recibe el `ConnectionManager` singleton del proceso."""
        self._connection_manager = connection_manager

    async def publicar(self, sesion_id: UUID, mensaje: dict[str, Any]) -> None:
        """Transmite `mensaje` a todas las conexiones activas del canal de `sesion_id`."""
        await self._connection_manager.enviar_a_sesion(sesion_id, mensaje)
