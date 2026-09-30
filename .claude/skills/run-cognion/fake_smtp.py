"""Servidor SMTP mínimo para smoke testing local — acepta cualquier mensaje.

No usa el módulo `smtpd` (removido en Python 3.12) ni requiere `aiosmtpd` (no instalado en
este entorno). Solo implementa el subconjunto de comandos que `smtplib.SMTP` necesita para
completar una entrega: EHLO/HELO, MAIL FROM, RCPT TO, DATA, QUIT.

Si se pasa `<log_file>`, cada mensaje capturado (headers + cuerpo, tal como los arma
`smtplib`) se agrega a ese archivo separado por una línea `-----MENSAJE-----`, para que
`smoke.sh` pueda verificar contenido real de un email (asunto, destinatario, cuerpo) — mismo
criterio de verificación que ya usan los tests de integración/BDD de `US-5.1.2`/`US-5.1.3`
contra un stub SMTP propio. Sin `<log_file>`, se comporta como antes: acepta y descarta.

Uso: python3 fake_smtp.py <puerto> [log_file]
"""

from __future__ import annotations

import socket
import sys


def _capturar_mensaje(conn: socket.socket, log_file: str | None) -> None:
    """Lee las líneas del bloque DATA hasta el terminador `.` y las persiste si corresponde."""
    buffer = b""
    lineas: list[str] = []
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            break
        buffer += chunk
        while b"\r\n" in buffer:
            linea, buffer = buffer.split(b"\r\n", 1)
            if linea == b".":
                if log_file:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write("-----MENSAJE-----\n")
                        f.write("\n".join(lineas))
                        f.write("\n")
                conn.sendall(b"250 OK\r\n")
                return
            lineas.append(linea.decode(errors="ignore"))


def _serve(port: int, log_file: str | None) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("localhost", port))
        server.listen(1)
        while True:
            conn, _ = server.accept()
            with conn:
                conn.sendall(b"220 fake-smtp ready\r\n")
                while True:
                    linea_cmd = conn.recv(4096)
                    if not linea_cmd:
                        break
                    cmd = linea_cmd.decode(errors="ignore").strip().upper()
                    if cmd.startswith("DATA"):
                        conn.sendall(b"354 End data with <CR><LF>.<CR><LF>\r\n")
                        _capturar_mensaje(conn, log_file)
                    elif cmd.startswith("QUIT"):
                        conn.sendall(b"221 Bye\r\n")
                        break
                    else:
                        conn.sendall(b"250 OK\r\n")


if __name__ == "__main__":
    _serve(int(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else None)
