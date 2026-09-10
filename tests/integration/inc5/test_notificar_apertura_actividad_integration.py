"""Test de integración end-to-end de la notificación de apertura (US-5.1.2).

Cubre los 4 escenarios de
`tests/features/inc5/US-5.1.2-notificacion-apertura.feature` contra el flujo HTTP real
(`POST /actividades`) con PostgreSQL real y un stub SMTP local — mismo patrón de servidor
SMTP embebido que `tests/integration/inc5/test_smtp_canal_envio_integration.py` (`US-5.1.1`),
duplicado localmente porque no hay `conftest.py` compartido en `tests/integration/inc5/`.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from src.app import app
from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil
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


def _periodo() -> tuple[str, str]:
    apertura = datetime.now(UTC)
    cierre = apertura + timedelta(days=7)
    return apertura.isoformat(), cierre.isoformat()


async def _crear_materia_con_preguntas(client: AsyncClient, headers: dict, cantidad: int) -> str:
    nombre = f"Ingeniería de Software {uuid.uuid4()}"
    creada = await client.post("/materias", json={"nombre": nombre}, headers=headers)
    banco_id = creada.json()["banco_id"]

    for i in range(cantidad):
        await client.post(
            "/preguntas/verdadero-falso",
            json={
                "banco_id": banco_id,
                "texto": f"Pregunta {i}",
                "respuesta_correcta": True,
                "unidad_tematica": "Unidad 1",
                "tema": "Tema",
                "dificultad": "medio",
                "importancia": "alto",
            },
            headers=headers,
        )

    return creada.json()["id"]


async def _crear_comision_con_estudiantes(
    session, materia_id: uuid.UUID, cantidad: int
) -> tuple[uuid.UUID, list[str]]:
    """Crea una comisión real para `materia_id` con `cantidad` estudiantes reales inscriptos."""
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    comision_repo = SQLAlchemyComisionRepository(session)
    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    comision = Comision.crear(materia_id, "lu 10-12", admin.id)
    await comision_repo.guardar(comision)

    emails = []
    for i in range(cantidad):
        email = f"estudiante{i}.{uuid.uuid4()}@fiuner.edu.ar"
        estudiante = Usuario.crear_estudiante(f"Estudiante {i}", email, "hash", comision.id)
        await usuario_repo.guardar(estudiante)
        emails.append(email)

    return comision.id, emails


class TestNotificarAperturaActividadIntegration:
    """Escenarios de `tests/features/inc5/US-5.1.2-notificacion-apertura.feature`."""

    async def test_actividad_restringida_a_comisiones_envia_un_email_por_estudiante(
        self, session, docente_headers, fake_smtp_server
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            comision_a_id, emails_a = await _crear_comision_con_estudiantes(
                session, uuid.UUID(materia_id), 2
            )
            comision_b_id, emails_b = await _crear_comision_con_estudiantes(
                session, uuid.UUID(materia_id), 1
            )
            apertura, cierre = _periodo()

            response = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                    "titulo": "Parcial 1",
                    "comisiones_ids": [str(comision_a_id), str(comision_b_id)],
                },
                headers=docente_headers,
            )

        assert response.status_code == 201
        assert len(fake_smtp_server.mensajes) == 3
        destinatarios_notificados = {
            mensaje.split("To: ")[1].split("\n")[0] for mensaje in fake_smtp_server.mensajes
        }
        assert destinatarios_notificados == set(emails_a) | set(emails_b)
        for mensaje in fake_smtp_server.mensajes:
            assert "Parcial 1" in mensaje

    async def test_actividad_sin_restriccion_envia_a_todas_las_comisiones_de_la_materia(
        self, session, docente_headers, fake_smtp_server
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            _comision_id, emails = await _crear_comision_con_estudiantes(
                session, uuid.UUID(materia_id), 2
            )
            apertura, cierre = _periodo()

            response = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=docente_headers,
            )

        assert response.status_code == 201
        assert len(fake_smtp_server.mensajes) == 2
        destinatarios_notificados = {
            mensaje.split("To: ")[1].split("\n")[0] for mensaje in fake_smtp_server.mensajes
        }
        assert destinatarios_notificados == set(emails)

    async def test_fallo_de_envio_smtp_no_aborta_la_creacion_de_la_actividad(
        self, session, docente_headers, monkeypatch
    ):
        # Puerto sin ningún servidor escuchando — el intento de conexión SMTP falla.
        monkeypatch.setattr(settings, "smtp_host", "127.0.0.1")
        monkeypatch.setattr(settings, "smtp_port", 1)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            await _crear_comision_con_estudiantes(session, uuid.UUID(materia_id), 1)
            apertura, cierre = _periodo()

            response = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=docente_headers,
            )

        assert response.status_code == 201

    async def test_materia_sin_comisiones_no_envia_ningun_email(
        self, docente_headers, fake_smtp_server
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura, cierre = _periodo()

            response = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=docente_headers,
            )

        assert response.status_code == 201
        assert fake_smtp_server.mensajes == []
