"""Arranca un `uvicorn` real como subproceso y captura su salida (US-ADJ-64).

`caplog` captura un mensaje de `logging` aunque el servidor real nunca lo muestre: eso dejó pasar el
hallazgo #2 de la UAT de `v0.9.0`. Estos tests leen lo que de verdad escribe el proceso.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class ServidorReal:
    """Un `uvicorn src.app:app` en otro proceso, con su salida en un archivo temporal."""

    def __init__(self, **entorno: str) -> None:
        """Prepara el proceso; no lo arranca hasta `iniciar()`."""
        self.puerto = _puerto_libre()
        self.url = f"http://127.0.0.1:{self.puerto}"
        self._entorno = {**os.environ, "PYTHONUNBUFFERED": "1", **entorno}
        self._archivo = Path(tempfile.mkstemp(prefix="uvicorn-adj64-", suffix=".log")[1])
        self._proceso: subprocess.Popen[bytes] | None = None

    def iniciar(self) -> None:
        """Arranca el servidor y espera a que responda `/health` (falla si el proceso muere)."""
        with self._archivo.open("wb") as salida:
            self._proceso = subprocess.Popen(  # noqa: S603
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "src.app:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(self.puerto),
                ],
                stdout=salida,
                stderr=subprocess.STDOUT,
                env=self._entorno,
            )
        limite = time.monotonic() + 30
        while time.monotonic() < limite:
            if self._proceso.poll() is not None:
                raise RuntimeError(f"el servidor terminó al arrancar:\n{self.salida()}")
            try:
                if httpx.get(f"{self.url}/health", timeout=1).status_code == 200:
                    return
            except httpx.TransportError:
                time.sleep(0.2)
        raise RuntimeError(f"el servidor no respondió a tiempo:\n{self.salida()}")

    def salida(self) -> str:
        """Todo lo que el proceso escribió hasta ahora."""
        return self._archivo.read_text(encoding="utf-8", errors="replace")

    def esperar_en_salida(self, texto: str, segundos: float = 5.0) -> str:
        """Espera hasta que `texto` aparezca en la salida y la devuelve (o la devuelve igual al vencer)."""
        limite = time.monotonic() + segundos
        while time.monotonic() < limite:
            if texto in self.salida():
                break
            time.sleep(0.1)
        return self.salida()

    def detener(self) -> None:
        """Termina el proceso y borra el archivo de salida."""
        if self._proceso is not None and self._proceso.poll() is None:
            self._proceso.terminate()
            try:
                self._proceso.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._proceso.kill()
        self._archivo.unlink(missing_ok=True)
