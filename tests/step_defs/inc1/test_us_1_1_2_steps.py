from __future__ import annotations

import asyncio
import threading

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import select, text

from src.app import app
from src.identidad.frameworks.db.models import InvitacionModel
from src.settings import settings
from src.shared.frameworks.db import SessionLocal

scenarios("../../features/inc1/US-1.1.2-registro-estudiante.feature")


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
        )
        return response.json()


async def _post(path: str, json: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json)


async def _crear_invitacion_vigente(materia: str) -> dict:
    admin = await _crear_usuario("admin.bdd112@fiuner.edu.ar", "administrador")
    docente = await _crear_usuario("docente.bdd112@fiuner.edu.ar", "docente")
    comision_resp = await _post(
        "/comisiones",
        {"materia": materia, "horario": "lu 10-12", "administrador_id": admin["id"]},
    )
    comision_id = comision_resp.json()["id"]
    await _post(f"/comisiones/{comision_id}/docentes", {"docente_id": docente["id"]})
    invitacion_resp = await _post(
        f"/comisiones/{comision_id}/invitaciones",
        {"docente_id": docente["id"], "email_destinatario": "estudiante.bdd112@fiuner.edu.ar"},
    )
    return {"comision_id": comision_id, **invitacion_resp.json()}


async def _token_de_invitacion(invitacion_id: str) -> str:
    async with SessionLocal() as session:
        resultado = await session.execute(
            select(InvitacionModel.token).where(InvitacionModel.id == invitacion_id)
        )
        return resultado.scalar_one()


async def _usada_en_de_invitacion(invitacion_id: str):
    async with SessionLocal() as session:
        resultado = await session.execute(
            select(InvitacionModel.usada_en).where(InvitacionModel.id == invitacion_id)
        )
        return resultado.scalar_one()


@given(parsers.parse('una Invitación vigente (no vencida, no usada) para la Comisión "{nombre}"'))
def invitacion_vigente_para_comision(context, nombre):
    invitacion = run_async(_crear_invitacion_vigente(nombre))
    context["invitacion_id"] = invitacion["id"]
    context["comision_id"] = invitacion["comision_id"]
    context["materia"] = nombre
    context["token"] = run_async(_token_de_invitacion(invitacion["id"]))


@given("una Invitación vigente")
def invitacion_vigente(context):
    invitacion = run_async(_crear_invitacion_vigente("IS-2026-C2"))
    context["invitacion_id"] = invitacion["id"]
    context["comision_id"] = invitacion["comision_id"]
    context["token"] = run_async(_token_de_invitacion(invitacion["id"]))


@given("un Usuario ya existe con el email que se intenta registrar")
def usuario_existente_con_email(context):
    context["email"] = "duplicado.bdd112@fiuner.edu.ar"
    run_async(_crear_usuario(context["email"], "docente"))


@when("el Estudiante ejecuta RegistrarEstudiante(token, nombre, email, password)")
def ejecuta_registrar_estudiante(context):
    context.setdefault("email", "nuevo.bdd112@fiuner.edu.ar")
    context["response"] = run_async(
        _post(
            "/identidad/registro",
            {
                "token": context["token"],
                "nombre": "Nico Estudiante",
                "email": context["email"],
                "password": "claveSegura1",
            },
        )
    )


@when("el Estudiante ejecuta RegistrarEstudiante con ese email")
def ejecuta_registrar_estudiante_con_email(context):
    context["response"] = run_async(
        _post(
            "/identidad/registro",
            {
                "token": context["token"],
                "nombre": "Nico Estudiante",
                "email": context["email"],
                "password": "claveSegura1",
            },
        )
    )


@then("el sistema crea un Usuario con perfil Estudiante en la misma transacción")
def valida_usuario_creado(context):
    assert context["response"].status_code == 201


@then(parsers.parse('Estudiante.comision_id queda asignado a "{nombre}"'))
def valida_comision_asignada(context, nombre):
    assert context["response"].json()["comision_id"] == context["comision_id"]
    assert context["materia"] == nombre


@then("la Invitación queda marcada como usada")
def valida_invitacion_usada(context):
    usada_en = run_async(_usada_en_de_invitacion(context["invitacion_id"]))
    assert usada_en is not None


@then("se emiten los eventos InvitacionAceptada y UsuarioRegistrado")
def valida_eventos_emitidos(context):
    assert context["response"].status_code == 201


@then("el Estudiante NO queda autenticado automáticamente")
def valida_sin_autenticacion_automatica(context):
    assert "token" not in context["response"].json()


@then(parsers.parse("el sistema rechaza la operación con {codigo_error}"))
def valida_rechazo_con_codigo(context, codigo_error):
    mapa_status = {"EmailYaRegistrado": 409}
    assert context["response"].status_code == mapa_status[codigo_error]


@then("la Invitación no se marca como usada")
def valida_invitacion_no_usada(context):
    usada_en = run_async(_usada_en_de_invitacion(context["invitacion_id"]))
    assert usada_en is None
