"""Servidor SMTP mínimo para smoke testing local — acepta cualquier mensaje y lo descarta.

No usa el módulo `smtpd` (removido en Python 3.12) ni requiere `aiosmtpd` (no instalado en
este entorno). Solo implementa el subconjunto de comandos que `smtplib.SMTP` necesita para
completar una entrega: EHLO/HELO, MAIL FROM, RCPT TO, DATA, QUIT.

Uso: python3 fake_smtp.py <puerto>
"""

from __future__ import annotations

import socket
import sys


def _serve(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("localhost", port))
        server.listen(1)
        while True:
            conn, _ = server.accept()
            with conn:
                conn.sendall(b"220 fake-smtp ready\r\n")
                in_data = False
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    if in_data:
                        if chunk.endswith(b"\r\n.\r\n"):
                            conn.sendall(b"250 OK\r\n")
                            in_data = False
                        continue
                    line = chunk.decode(errors="ignore").strip().upper()
                    if line.startswith("DATA"):
                        conn.sendall(b"354 End data with <CR><LF>.<CR><LF>\r\n")
                        in_data = True
                    elif line.startswith("QUIT"):
                        conn.sendall(b"221 Bye\r\n")
                        break
                    else:
                        conn.sendall(b"250 OK\r\n")


if __name__ == "__main__":
    _serve(int(sys.argv[1]))
