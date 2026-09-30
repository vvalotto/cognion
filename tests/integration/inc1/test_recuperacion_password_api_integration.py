import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.app import app
from src.identidad.frameworks.db.models import TokenRecuperacionPasswordModel
from src.settings import settings


async def _handle_fake_smtp(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Acepta cualquier comando SMTP y responde OK — evita depender de un SMTP real."""
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
            while True:
                data_line = await reader.readline()
                if data_line.strip() == b".":
                    writer.write(b"250 OK queued\r\n")
                    await writer.drain()
                    break
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
    """Levanta un stub SMTP local y apunta `settings` a él durante el test."""
    server = await asyncio.start_server(_handle_fake_smtp, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    monkeypatch.setattr(settings, "smtp_host", "127.0.0.1")
    monkeypatch.setattr(settings, "smtp_port", port)

    async with server:
        task = asyncio.ensure_future(server.serve_forever())
        yield
        task.cancel()


class TestRecuperacionPasswordAPIIntegration:
    async def test_solicitar_con_email_de_cuenta_existente(
        self, fake_smtp_server, admin_headers, session
    ):
        transport = ASGITransport(app=app)
        email = f"docente.rec.{uuid.uuid4()}@fiuner.edu.ar"
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/usuarios",
                json={
                    "nombre": "Docente Recuperación",
                    "email": email,
                    "password": "claveSegura1#",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )

            response = await client.post(
                "/identidad/recuperar-password/solicitar",
                json={"email": email},
            )

        assert response.status_code == 202
        resultado = await session.execute(
            select(TokenRecuperacionPasswordModel).where(
                TokenRecuperacionPasswordModel.usado_en.is_(None)
            )
        )
        tokens = resultado.scalars().all()
        assert len(tokens) == 1

    async def test_solicitar_con_email_inexistente_responde_igual(self, admin_headers, session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/identidad/recuperar-password/solicitar",
                json={"email": f"inexistente.{uuid.uuid4()}@fiuner.edu.ar"},
            )

        assert response.status_code == 202
        resultado = await session.execute(select(TokenRecuperacionPasswordModel))
        assert resultado.scalars().all() == []

    async def test_solicitar_dos_veces_invalida_el_token_anterior(
        self, fake_smtp_server, admin_headers, session
    ):
        transport = ASGITransport(app=app)
        email = f"docente.rec2.{uuid.uuid4()}@fiuner.edu.ar"
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/usuarios",
                json={
                    "nombre": "Docente Recuperación",
                    "email": email,
                    "password": "claveSegura1#",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )

            await client.post("/identidad/recuperar-password/solicitar", json={"email": email})
            await client.post("/identidad/recuperar-password/solicitar", json={"email": email})

        resultado = await session.execute(select(TokenRecuperacionPasswordModel))
        tokens = resultado.scalars().all()
        assert len(tokens) == 2
        sin_usar = [t for t in tokens if t.usado_en is None]
        assert len(sin_usar) == 1

    async def test_fallo_de_smtp_no_bloquea_la_respuesta(self, admin_headers, session):
        """Sin `fake_smtp_server`: el host SMTP real no responde — el envío falla igual."""
        transport = ASGITransport(app=app)
        email = f"docente.rec3.{uuid.uuid4()}@fiuner.edu.ar"
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/usuarios",
                json={
                    "nombre": "Docente Recuperación",
                    "email": email,
                    "password": "claveSegura1#",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )

            response = await client.post(
                "/identidad/recuperar-password/solicitar",
                json={"email": email},
            )

        assert response.status_code == 202
        resultado = await session.execute(select(TokenRecuperacionPasswordModel))
        assert len(resultado.scalars().all()) == 1
