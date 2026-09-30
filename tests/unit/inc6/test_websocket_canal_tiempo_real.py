"""Tests unitarios de `WebSocketCanalTiempoReal` (US-6.1.1) — delega en `ConnectionManager`."""

from unittest.mock import AsyncMock
from uuid import uuid4

from src.actividad_evaluativa.frameworks.websockets.websocket_canal_tiempo_real import (
    WebSocketCanalTiempoReal,
)


class TestPublicar:
    async def test_delega_en_el_connection_manager(self):
        connection_manager = AsyncMock()
        canal = WebSocketCanalTiempoReal(connection_manager)
        sesion_id = uuid4()
        mensaje = {"tipo": "prueba"}

        await canal.publicar(sesion_id, mensaje)

        connection_manager.enviar_a_sesion.assert_awaited_once_with(sesion_id, mensaje)
