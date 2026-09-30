"""Cliente WebSocket de consola para la revisión manual de la sesión en vivo (US-6.2.9).

Se conecta al canal de una sesión y escribe cada mensaje que llega, una línea por mensaje, con el
nombre del cliente. Corre hasta que lo cortan (Ctrl+C / kill). Lo usa `guion_manual_iteracion2.sh`,
que lanza uno por participante en background y muestra sus logs paso a paso.

Uso: PYTHONPATH=. .venv/bin/python tests/uat/inc6/cliente_ws.py <ws_url> <token> <nombre>
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime

import websockets


async def escuchar(ws_url: str, token: str, nombre: str) -> None:
    """Imprime cada mensaje recibido del canal hasta que el servidor o el usuario cortan."""
    async with websockets.connect(f"{ws_url}?token={token}") as websocket:
        print(f"[{nombre}] conectado", flush=True)
        async for crudo in websocket:
            mensaje = json.loads(crudo)
            hora = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(
                f"[{nombre}] {hora} {mensaje['tipo']}: "
                f"{json.dumps(mensaje, ensure_ascii=False)}",
                flush=True,
            )


if __name__ == "__main__":
    url, token, nombre = sys.argv[1:4]
    try:
        asyncio.run(escuchar(url, token, nombre))
    except (KeyboardInterrupt, websockets.ConnectionClosed):
        print(f"[{nombre}] desconectado", flush=True)
