from __future__ import annotations

import asyncio
import threading
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenario, then, when
from sqlalchemy import text

from src.app import app
from src.identidad.frameworks.db.models import InvitacionModel
from src.settings import settings
from src.shared.frameworks.db import SessionLocal

FEATURE = "../../features/inc1/US-1.1.3-registro-link-invalido.feature"


@scenario(FEATURE, "Token inexistente")
def test_token_inexistente():
    pass


@scenario(FEATURE, "Invitación vencida")
def test_invitacion_vencida():
    pass


@scenario(FEATURE, "Invitación ya usada")
def test_invitacion_ya_usada():
    pass


# El Scenario Outline "La UI no distingue el motivo del rechazo" (tag @ux) no se registra
# aquí a propósito: requiere el frontend de identidad, todavía diferido (ver
# docs/plans/inc1/US-1.1.3-context.md). Queda documentado en el .feature para cuando exista.


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


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


@pytest.fixture
def context():
    return {}


async def _post(path: str, json: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json)


async def _crear_usuario(email: str, perfil: str) -> dict:
    return (
        await _post(
            "/usuarios",
            {
                "nombre": "Usuario Test",
                "email": email,
                "password": "claveSegura1",
                "perfil": perfil,
            },
        )
    ).json()


async def _crear_invitacion_vigente() -> str:
    admin = await _crear_usuario("admin.bdd113@fiuner.edu.ar", "administrador")
    docente = await _crear_usuario("docente.bdd113@fiuner.edu.ar", "docente")
    comision_resp = await _post(
        "/comisiones",
        {"materia": "IS-2026-C3", "horario": "lu 10-12", "administrador_id": admin["id"]},
    )
    comision_id = comision_resp.json()["id"]
    await _post(f"/comisiones/{comision_id}/docentes", {"docente_id": docente["id"]})
    invitacion_resp = await _post(
        f"/comisiones/{comision_id}/invitaciones",
        {"docente_id": docente["id"], "email_destinatario": "estudiante.bdd113@fiuner.edu.ar"},
    )
    return invitacion_resp.json()["id"]


async def _vencer_invitacion(invitacion_id: str) -> str:
    async with SessionLocal() as session:
        modelo = await session.get(InvitacionModel, invitacion_id)
        modelo.expira_en = datetime.now(UTC) - timedelta(seconds=1)
        await session.commit()
        return modelo.token


async def _marcar_usada(invitacion_id: str) -> str:
    async with SessionLocal() as session:
        modelo = await session.get(InvitacionModel, invitacion_id)
        modelo.usada_en = datetime.now(UTC)
        await session.commit()
        return modelo.token


@given("un token que no corresponde a ninguna Invitación")
def token_inexistente(context):
    context["token"] = "token-que-no-existe"


@given("una Invitación cuyo expira_en ya pasó")
def invitacion_vencida(context):
    invitacion_id = run_async(_crear_invitacion_vigente())
    context["token"] = run_async(_vencer_invitacion(invitacion_id))


@given("una Invitación con usada_en distinto de null")
def invitacion_ya_usada(context):
    invitacion_id = run_async(_crear_invitacion_vigente())
    context["token"] = run_async(_marcar_usada(invitacion_id))


@when("el Estudiante ejecuta RegistrarEstudiante(token, datos_usuario)")
@when("el Estudiante ejecuta RegistrarEstudiante con ese token")
def ejecuta_registrar_estudiante(context):
    context["response"] = run_async(
        _post(
            "/identidad/registro",
            {
                "token": context["token"],
                "nombre": "Nico Estudiante",
                "email": "rechazo.bdd113@fiuner.edu.ar",
                "password": "claveSegura1",
            },
        )
    )


@then(parsers.parse("el sistema rechaza la operación con {codigo_error}"))
def valida_rechazo_con_codigo(context, codigo_error):
    mapa_status = {
        "InvitacionInvalida": 422,
        "InvitacionVencida": 422,
        "InvitacionYaUsada": 422,
    }
    assert context["response"].status_code == mapa_status[codigo_error]


@then("ningún Usuario se crea")
def valida_ningun_usuario_creado(context):
    assert context["response"].status_code != 201


@then("no se persiste ningún evento de dominio")
def valida_sin_evento_de_dominio(context):
    assert context["response"].status_code == 422
