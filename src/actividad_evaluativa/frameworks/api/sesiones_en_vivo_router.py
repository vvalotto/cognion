"""Router de infraestructura de tiempo real de sesiones en vivo (`US-6.1.1`).

Arranca solo con el canal de broadcast por WebSocket — `US-6.1.2` a `US-6.1.4` agregan acá los
endpoints HTTP de negocio (crear, unirse, iniciar).
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from src.actividad_evaluativa.frameworks.dependencies import (
    get_connection_manager,
    get_jwt_issuer,
)
from src.shared.entities.errors import JWTExpirado, JWTInvalido

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sesiones-en-vivo", tags=["actividad_evaluativa_en_vivo"])


@router.websocket("/{sesion_id}/canal")
async def canal_sesion_en_vivo(
    websocket: WebSocket, sesion_id: UUID, token: str | None = None
) -> None:
    """Suscribe al cliente al canal de broadcast de `sesion_id`, autenticado por JWT.

    El JWT viaja como query param (`?token=...`) — la API nativa `WebSocket` del navegador no
    permite fijar el header `Authorization` en el handshake (`US-6.1.1`). Se rechaza la
    conexión con el código `1008` (política violada) si el token falta, es inválido o expiró —
    sin verificación de rol adicional: Docente y Estudiante comparten el mismo canal de lectura
    (`BC-actividad-evaluativa-modelo.md` §16).
    """
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        get_jwt_issuer().verificar(token)
    except (JWTInvalido, JWTExpirado):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    connection_manager = get_connection_manager()
    await connection_manager.conectar(sesion_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.desconectar(sesion_id, websocket)
