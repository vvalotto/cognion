import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from src.app import app
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


class TestInvitacionesAPIIntegration:
    async def test_flujo_completo_generar_invitacion(
        self, fake_smtp_server, admin_headers, docente_headers
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            admin_resp = await client.post(
                "/usuarios",
                json={
                    "nombre": "Admin",
                    "email": "admin.inv@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "administrador",
                },
                headers=admin_headers,
            )
            admin_id = admin_resp.json()["id"]

            docente_resp = await client.post(
                "/usuarios",
                json={
                    "nombre": "Ana Docente",
                    "email": "docente.inv@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )
            docente_id = docente_resp.json()["id"]

            comision_resp = await client.post(
                "/comisiones",
                json={"materia": "IS", "horario": "lu 10-12", "administrador_id": admin_id},
                headers=admin_headers,
            )
            comision_id = comision_resp.json()["id"]

            await client.post(
                f"/comisiones/{comision_id}/docentes",
                json={"docente_id": docente_id},
                headers=admin_headers,
            )

            response = await client.post(
                f"/comisiones/{comision_id}/invitaciones",
                json={"docente_id": docente_id, "email_destinatario": "estudiante@fiuner.edu.ar"},
                headers=docente_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["comision_id"] == comision_id
        assert data["docente_id"] == docente_id
        assert "expira_en" in data

    async def test_docente_no_asignado_devuelve_422(
        self, fake_smtp_server, admin_headers, docente_headers
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            admin_resp = await client.post(
                "/usuarios",
                json={
                    "nombre": "Admin",
                    "email": "admin2.inv@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "administrador",
                },
                headers=admin_headers,
            )
            admin_id = admin_resp.json()["id"]

            docente_resp = await client.post(
                "/usuarios",
                json={
                    "nombre": "Docente Sin Asignar",
                    "email": "docente2.inv@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )
            docente_id = docente_resp.json()["id"]

            comision_resp = await client.post(
                "/comisiones",
                json={"materia": "IS", "horario": "lu 10-12", "administrador_id": admin_id},
                headers=admin_headers,
            )
            comision_id = comision_resp.json()["id"]

            response = await client.post(
                f"/comisiones/{comision_id}/invitaciones",
                json={"docente_id": docente_id, "email_destinatario": "estudiante@fiuner.edu.ar"},
                headers=docente_headers,
            )

        assert response.status_code == 422

    async def test_comision_inexistente_devuelve_404(
        self, fake_smtp_server, admin_headers, docente_headers
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            docente_resp = await client.post(
                "/usuarios",
                json={
                    "nombre": "Docente",
                    "email": "docente3.inv@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )
            docente_id = docente_resp.json()["id"]

            response = await client.post(
                "/comisiones/00000000-0000-0000-0000-000000000000/invitaciones",
                json={"docente_id": docente_id, "email_destinatario": "estudiante@fiuner.edu.ar"},
                headers=docente_headers,
            )

        assert response.status_code == 404
