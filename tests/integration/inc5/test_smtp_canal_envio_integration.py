"""Test de integración de `SmtpCanalEnvio` contra un servidor SMTP-stub local (US-5.1.1).

Cubre el escenario "Envío real contra el SMTP local de prueba" de
`tests/features/inc5/US-5.1.1-infraestructura-notificaciones.feature` sin depender de
Mailhog/Mailtrap (no instalado en este entorno) — mismo patrón de servidor SMTP embebido que
`tests/integration/inc1/test_invitaciones_api_integration.py::fake_smtp_server`, extendido
para capturar el contenido del mensaje recibido y poder verificar asunto/destinatario/cuerpo.
"""

from __future__ import annotations

import asyncio

import pytest

from src.notificaciones.frameworks.adapters.smtp_canal_envio import SmtpCanalEnvio
from src.settings import settings


class _BandejaSmtp:
    """Acumula los mensajes DATA recibidos por el stub, decodificados como texto."""

    def __init__(self) -> None:
        self.mensajes: list[str] = []


async def _handle_fake_smtp(
    bandeja: _BandejaSmtp, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    """Acepta cualquier comando SMTP, capturando el contenido de cada `DATA` en `bandeja`."""
    writer.write(b"220 fake.smtp ESMTP\r\n")
    await writer.drain()
    while True:
        line = await reader.readline()
        if not line:
            break
        cmd = line.decode(errors="ignore").strip().upper()
        if cmd.startswith("DATA"):
            writer.write(b"354 End data with <CR><LF>.<CR><LF>\r\n")
            await writer.drain()
            lineas_mensaje: list[str] = []
            while True:
                data_line = await reader.readline()
                if data_line.strip() == b".":
                    bandeja.mensajes.append("\n".join(lineas_mensaje))
                    writer.write(b"250 OK queued\r\n")
                    await writer.drain()
                    break
                lineas_mensaje.append(data_line.decode(errors="ignore").rstrip("\r\n"))
        elif cmd.startswith("QUIT"):
            writer.write(b"221 Bye\r\n")
            await writer.drain()
            writer.close()
            return
        else:
            writer.write(b"250 OK\r\n")
            await writer.drain()


@pytest.fixture
async def fake_smtp_server(monkeypatch):
    """Levanta un stub SMTP local con bandeja capturable y apunta `settings` a él."""
    bandeja = _BandejaSmtp()

    async def _handler(reader, writer):
        await _handle_fake_smtp(bandeja, reader, writer)

    server = await asyncio.start_server(_handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    monkeypatch.setattr(settings, "smtp_host", "127.0.0.1")
    monkeypatch.setattr(settings, "smtp_port", port)

    async with server:
        task = asyncio.ensure_future(server.serve_forever())
        yield bandeja
        task.cancel()


class TestSmtpCanalEnvioIntegration:
    async def test_envio_real_contra_smtp_local_de_prueba(self, fake_smtp_server):
        bandeja = fake_smtp_server
        canal = SmtpCanalEnvio()

        await canal.enviar("estudiante@example.com", "Asunto de prueba", "Cuerpo de prueba")

        assert len(bandeja.mensajes) == 1
        mensaje = bandeja.mensajes[0]
        assert "Subject: Asunto de prueba" in mensaje
        assert "To: estudiante@example.com" in mensaje
        assert "Cuerpo de prueba" in mensaje
