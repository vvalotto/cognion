"""Steps BDD de US-ADJ-36 — Contraseña segura, política ampliada (INV-ID-11)."""

from __future__ import annotations

import asyncio
import threading
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.identidad.entities.errors import PasswordDemasiadoCorta, PasswordSinComplejidadSuficiente
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.db.models import InvitacionModel
from src.settings import settings
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc1._auth_headers import admin_headers, docente_headers

scenarios("../../features/inc5-adj/US-ADJ-36-contrasena-segura.feature")

_NOMBRES_EXCEPCION = {
    "PasswordDemasiadoCorta": PasswordDemasiadoCorta,
    "PasswordSinComplejidadSuficiente": PasswordSinComplejidadSuficiente,
}


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
    """Levanta un stub SMTP en un thread con loop propio — `GenerarInvitacion` envía email
    real (`ADR-012`); mismo patrón que `tests/step_defs/inc4-adj/test_us_adj_26_steps.py`."""
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


async def _post(path: str, json: dict, headers: dict[str, str] | None = None):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json, headers=headers)


async def _crear_usuario_api(email: str, perfil: str) -> dict:
    return (
        await _post(
            "/usuarios",
            {
                "nombre": "Usuario BDD",
                "email": email,
                "password": "ClaveSegura#Adj36",
                "perfil": perfil,
            },
            headers=admin_headers(),
        )
    ).json()


async def _crear_materia(sufijo: str) -> str:
    respuesta = await _post(
        "/materias", {"nombre": f"IS-2026-ADJ36-{sufijo}"}, headers=docente_headers()
    )
    return respuesta.json()["id"]


async def _crear_invitacion_vigente() -> str:
    sufijo = uuid.uuid4()
    admin = await _crear_usuario_api(f"admin.bddadj36.{sufijo}@fiuner.edu.ar", "administrador")
    docente = await _crear_usuario_api(f"docente.bddadj36.{sufijo}@fiuner.edu.ar", "docente")
    materia_id = await _crear_materia(str(sufijo))
    comision_resp = await _post(
        "/comisiones",
        {"materia_id": materia_id, "horario": "lu 10-12", "administrador_id": admin["id"]},
        headers=admin_headers(),
    )
    comision_id = comision_resp.json()["id"]
    await _post(
        f"/comisiones/{comision_id}/docentes",
        {"docente_id": docente["id"]},
        headers=admin_headers(),
    )
    invitacion_resp = await _post(
        f"/comisiones/{comision_id}/invitaciones",
        {"docente_id": docente["id"], "email_destinatario": "estudiante.bddadj36@fiuner.edu.ar"},
        headers=docente_headers(),
    )
    invitacion_id = invitacion_resp.json()["id"]
    async with SessionLocal() as session:
        modelo = await session.get(InvitacionModel, invitacion_id)
        return modelo.token, modelo.usada_en


# --- Escenarios de dominio puro (Usuario.validar_password_nueva) ---------------


@given(parsers.parse('una contraseña nueva "{password}"'))
def dada_una_password(context, password):
    context["password"] = password


@when("se valida con Usuario.validar_password_nueva")
def valida_password(context):
    try:
        Usuario.validar_password_nueva(context["password"])
        context["excepcion"] = None
    except (PasswordDemasiadoCorta, PasswordSinComplejidadSuficiente) as exc:
        context["excepcion"] = exc


@then("la validación no lanza ninguna excepción")
def valida_sin_excepcion(context):
    assert context["excepcion"] is None


@then(parsers.parse("el sistema rechaza con {nombre_excepcion}"))
def valida_rechazo(context, nombre_excepcion):
    excepcion_esperada = _NOMBRES_EXCEPCION[nombre_excepcion]
    if "response" in context:
        assert context["response"].status_code == 422
    else:
        assert isinstance(context["excepcion"], excepcion_esperada)


# --- Escenarios de alta de Docente (gap cerrado — CrearUsuarioUseCase) ---------


@given("un Administrador autenticado")
def dado_un_administrador(context):
    context["headers"] = admin_headers()


@when(parsers.parse('ejecuta CrearUsuario con password "{password}" y perfil Docente'))
def ejecuta_crear_usuario(context, password):
    context["email"] = "nuevo.docente.bddadj36@fiuner.edu.ar"
    context["response"] = run_async(
        _post(
            "/usuarios",
            {
                "nombre": "Nuevo Docente",
                "email": context["email"],
                "password": password,
                "perfil": "docente",
            },
            headers=context["headers"],
        )
    )


@then("el Usuario se crea exitosamente")
def valida_usuario_creado(context):
    assert context["response"].status_code == 201


@then("ningún Usuario se crea")
def valida_ningun_usuario_creado(context):
    assert context["response"].status_code == 422


# --- Escenarios de registro de Estudiante (gap cerrado — RegistrarEstudianteUseCase) --


@given("una Invitación vigente para una Comisión")
def dada_una_invitacion_vigente(context):
    token, _usada_en = run_async(_crear_invitacion_vigente())
    context["token"] = token


@when(parsers.parse('ejecuta RegistrarEstudiante con password "{password}"'))
def ejecuta_registrar_estudiante(context, password):
    context["response"] = run_async(
        _post(
            "/identidad/registro",
            {
                "token": context["token"],
                "nombre": "Nuevo Estudiante",
                "email": "nuevo.estudiante.bddadj36@fiuner.edu.ar",
                "password": password,
            },
        )
    )


@then("el Usuario se crea exitosamente con perfil Estudiante")
def valida_estudiante_creado(context):
    assert context["response"].status_code == 201
    assert context["response"].json()["comision_id"] is not None


@then("la Invitación sigue sin usarse")
def valida_invitacion_sin_usar(context):
    async def _obtener_usada_en():
        async with SessionLocal() as session:
            resultado = await session.execute(
                text("SELECT usada_en FROM invitacion WHERE token = :token"),
                {"token": context["token"]},
            )
            return resultado.scalar_one()

    assert run_async(_obtener_usada_en()) is None
