"""Corre un comando bajo un pseudoterminal real y le escribe como lo haría una persona (US-ADJ-65).

`getpass` solo funciona "de verdad" con una terminal de control: por eso `pty.fork()` y no un pipe.
Con entradas guiadas los tests unitarios no pueden comprobar que el comando realmente pida dos veces.
"""

from __future__ import annotations

import os
import pty
import select
import signal
import sys
import time


class TerminalSimulada:
    """Ejecuta `python -m <modulo>` en un pty; `esperar` lee la salida y `escribir` teclea."""

    def __init__(self, modulo: str, entorno: dict[str, str]) -> None:
        """Lanza el proceso hijo con una terminal de control propia."""
        self._salida = ""
        self._cursor = 0  # hasta dónde se consumió: `esperar` busca solo lo que llegó después
        pid, fd = pty.fork()
        if pid == 0:  # hijo: ya tiene el pty como terminal de control
            os.execvpe(sys.executable, [sys.executable, "-m", modulo], {**os.environ, **entorno})
        self._pid, self._fd = pid, fd
        self.codigo: int | None = None

    def esperar(self, texto: str, segundos: float = 20.0) -> bool:
        """Espera a que `texto` aparezca **después** de lo ya consumido; `True` si llegó a tiempo.

        Así dos pedidos iguales seguidos ("Contraseña…" dos veces) no se confunden entre sí.
        """
        limite = time.monotonic() + segundos
        while time.monotonic() < limite:
            posicion = self._salida.find(texto, self._cursor)
            if posicion >= 0:
                self._cursor = posicion + len(texto)
                return True
            self._leer(0.2)
        return False

    def escribir(self, linea: str) -> None:
        """Teclea una línea y Enter."""
        os.write(self._fd, (linea + "\n").encode())

    def terminar(self, segundos: float = 20.0) -> int:
        """Espera el fin del proceso, devuelve su código de salida y lo mata si no termina."""
        limite = time.monotonic() + segundos
        while self.codigo is None and time.monotonic() < limite:
            self._leer(0.2)
            pid, estado = os.waitpid(self._pid, os.WNOHANG)
            if pid:
                self.codigo = os.waitstatus_to_exitcode(estado)
        if self.codigo is None:
            os.kill(self._pid, signal.SIGKILL)
            os.waitpid(self._pid, 0)
            self.codigo = -1
        self._leer(0.2)
        os.close(self._fd)
        return self.codigo

    @property
    def salida(self) -> str:
        """Todo lo que el proceso mostró en la terminal."""
        return self._salida

    def _leer(self, espera: float) -> None:
        listo, _, _ = select.select([self._fd], [], [], espera)
        if listo:
            try:
                self._salida += os.read(self._fd, 4096).decode(errors="replace")
            except OSError:  # el hijo cerró su lado de la terminal
                pass
