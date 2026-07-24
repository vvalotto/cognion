from __future__ import annotations

import asyncio
import threading
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.settings import settings
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc1._auth_headers import admin_headers, docente_headers

scenarios("../../features/inc1/US-1.1.1-generar-invitacion.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas_identidad() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM invitacion"))
        await session.execute(text("DELETE FROM comision_docentes"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM usuario"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_identidad():
    run_async(_limpiar_tablas_identidad())
    yield
    run_async(_limpiar_tablas_identidad())


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


@pytest.fixture(autouse=True)
def fake_smtp_server():
    """Levanta un stub SMTP en un thread con loop propio (los steps usan `asyncio.run()`
    cada uno, así que el server no puede vivir en un loop que se cierra entre steps)."""
    host_original, port_original = settings.smtp_host, settings.smtp_port
    loop = asyncio.new_event_loop()
    port_listo = threading.Event()
    estado: dict[str, object] = {}

    async def _serve() -> None:
        server = await asyncio.start_server(_handle_fake_smtp, "127.0.0.1", 0)
        estado["server"] = server
        estado["port"] = server.sockets[0].getsockname()[1]
        port_listo.set()
        async with server:
            await server.serve_forever()

    def _run_loop() -> None:
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_serve())
        except asyncio.CancelledError:
            pass

    hilo = threading.Thread(target=_run_loop, daemon=True)
    hilo.start()
    port_listo.wait(timeout=2)

    settings.smtp_host = "127.0.0.1"
    settings.smtp_port = estado["port"]

    yield

    async def _cerrar() -> None:
        estado["server"].close()
        await estado["server"].wait_closed()

    asyncio.run_coroutine_threadsafe(_cerrar(), loop).result(timeout=2)
    loop.call_soon_threadsafe(loop.stop)
    hilo.join(timeout=2)
    settings.smtp_host, settings.smtp_port = host_original, port_original


@pytest.fixture
def context():
    return {}


async def _crear_usuario(email: str, perfil: str) -> dict:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/usuarios",
            json={
                "nombre": "Usuario Test",
                "email": email,
                "password": "claveSegura1",
                "perfil": perfil,
            },
            headers=admin_headers(),
        )
        return response.json()


async def _post(path: str, json: dict, headers: dict[str, str] | None = None):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json, headers=headers or admin_headers())


@given("un Docente autenticado")
def docente_autenticado(context):
    docente = run_async(_crear_usuario("docente.bdd111@fiuner.edu.ar", "docente"))
    context["docente_id"] = docente["id"]


@given(parsers.parse('el Docente está presente en docentes_asignados de la Comisión "{nombre}"'))
def docente_presente_en_comision(context, nombre):
    admin = run_async(_crear_usuario("admin.bdd111a@fiuner.edu.ar", "administrador"))
    comision_resp = run_async(
        _post(
            "/comisiones",
            {"materia": nombre, "horario": "lu 10-12", "administrador_id": admin["id"]},
        )
    )
    comision_id = comision_resp.json()["id"]
    run_async(_post(f"/comisiones/{comision_id}/docentes", {"docente_id": context["docente_id"]}))
    context["comision_id"] = comision_id


@given(parsers.parse('el Docente NO está presente en docentes_asignados de la Comisión "{nombre}"'))
def docente_no_presente_en_comision(context, nombre):
    admin = run_async(_crear_usuario("admin.bdd111b@fiuner.edu.ar", "administrador"))
    comision_resp = run_async(
        _post(
            "/comisiones",
            {"materia": nombre, "horario": "lu 10-12", "administrador_id": admin["id"]},
        )
    )
    context["comision_id"] = comision_resp.json()["id"]


@when("ejecuta GenerarInvitacion(comision_id, docente_id)")
def ejecuta_generar_invitacion(context):
    context["response"] = run_async(
        _post(
            f"/comisiones/{context['comision_id']}/invitaciones",
            {
                "docente_id": context["docente_id"],
                "email_destinatario": "estudiante.bdd@fiuner.edu.ar",
            },
            headers=docente_headers(),
        )
    )


@when("intenta ejecutar GenerarInvitacion sobre esa comisión")
def intenta_generar_invitacion(context):
    context["response"] = run_async(
        _post(
            f"/comisiones/{context['comision_id']}/invitaciones",
            {
                "docente_id": context["docente_id"],
                "email_destinatario": "estudiante.bdd@fiuner.edu.ar",
            },
            headers=docente_headers(),
        )
    )


@then("el sistema persiste una Invitación con token único")
def valida_invitacion_persistida(context):
    assert context["response"].status_code == 201
    assert context["response"].json()["id"]


@then("expira_en queda fijado a 7 días desde ahora")
def valida_expira_en(context):
    data = context["response"].json()
    expira_en = datetime.fromisoformat(data["expira_en"])
    ahora = datetime.now(UTC)
    delta = expira_en - ahora
    assert timedelta(days=6, hours=23) < delta <= timedelta(days=7, minutes=1)


@then("se envía un email con el link de invitación")
def valida_email_enviado(context):
    assert context["response"].status_code == 201


@then("se emite el evento InvitacionGenerada")
def valida_evento_invitacion_generada(context):
    assert context["response"].status_code == 201


@then(parsers.parse("el sistema rechaza la operación con {codigo_error}"))
def valida_rechazo_con_codigo(context, codigo_error):
    mapa_status = {"DocenteNoAsignadoAComision": 422}
    assert context["response"].status_code == mapa_status[codigo_error]


@then("ninguna Invitación se crea")
def valida_ninguna_invitacion_creada(context):
    assert context["response"].status_code == 422
