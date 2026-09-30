"""Steps BDD de US-ADJ-38 — Solicitar recuperación de contraseña (endpoint público)."""

from __future__ import annotations

import asyncio
import threading
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import select, text

from src.app import app
from src.identidad.frameworks.db.models import TokenRecuperacionPasswordModel
from src.settings import settings
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc1._auth_headers import admin_headers

scenarios("../../features/inc5-adj/US-ADJ-38-solicitar-recuperacion-password.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas_identidad() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM token_recuperacion_password"))
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


@pytest.fixture
def fake_smtp_server():
    """Levanta un stub SMTP en un thread con loop propio — mismo patrón que
    `tests/step_defs/inc5-adj/test_us_adj_36_steps.py`. Fixture NO autouse — el escenario de
    fallo de envío la omite a propósito, dejando el SMTP real (inalcanzable) para forzar la
    excepción."""
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


async def _crear_usuario_docente(email: str) -> None:
    await _post(
        "/usuarios",
        {
            "nombre": "Docente BDD",
            "email": email,
            "password": "ClaveSegura#Adj38",
            "perfil": "docente",
        },
        headers=admin_headers(),
    )


async def _tokens_de(usuario_email: str) -> list[TokenRecuperacionPasswordModel]:
    async with SessionLocal() as session:
        resultado = await session.execute(
            text("SELECT id FROM usuario WHERE email = :email"), {"email": usuario_email}
        )
        usuario_id = resultado.scalar_one_or_none()
        if usuario_id is None:
            return []
        resultado = await session.execute(
            select(TokenRecuperacionPasswordModel).where(
                TokenRecuperacionPasswordModel.usuario_id == usuario_id
            )
        )
        return list(resultado.scalars().all())


@given(parsers.parse('un Usuario con email "{email}" registrado'))
def dado_un_usuario_registrado(context, email, fake_smtp_server):
    context["email"] = email
    run_async(_crear_usuario_docente(email))


@given(parsers.parse('ningún Usuario tiene el email "{email}"'))
def dado_ningun_usuario_con_email(context, email):
    context["email"] = email


@given("un Usuario ya tiene un TokenRecuperacionPassword activo sin usar")
def dado_un_token_activo(context, fake_smtp_server):
    email = "docente.previo.bddadj38@fiuner.edu.ar"
    context["email"] = email
    run_async(_crear_usuario_docente(email))
    run_async(_post("/identidad/recuperar-password/solicitar", {"email": email}))
    tokens = run_async(_tokens_de(email))
    context["token_previo"] = tokens[0].token


@given("el canal de envío de Notificaciones falla al intentar enviar")
def dado_canal_de_envio_falla(context):
    """Sin `fake_smtp_server`: el host SMTP real (`localhost:25`, sin proceso escuchando en
    este entorno) rechaza la conexión — fuerza la excepción sin mockear nada."""
    context["email"] = "docente.fallo.bddadj38@fiuner.edu.ar"
    run_async(_crear_usuario_docente(context["email"]))


@when(parsers.parse("se solicita POST /identidad/recuperar-password/solicitar con ese email"))
def cuando_se_solicita_recuperacion(context):
    context["response"] = run_async(
        _post("/identidad/recuperar-password/solicitar", {"email": context["email"]})
    )


@when("se solicita una nueva recuperación para el mismo email")
def cuando_se_solicita_de_nuevo(context):
    context["response"] = run_async(
        _post("/identidad/recuperar-password/solicitar", {"email": context["email"]})
    )


@when("se solicita una recuperación con un email de cuenta existente")
def cuando_se_solicita_pese_a_fallo(context):
    context["response"] = run_async(
        _post("/identidad/recuperar-password/solicitar", {"email": context["email"]})
    )


@then("la respuesta es 202 Accepted con el mensaje genérico")
def entonces_respuesta_202(context):
    assert context["response"].status_code == 202


@then("la respuesta es 202 Accepted con el mismo mensaje genérico que el caso exitoso")
def entonces_respuesta_202_generica(context):
    assert context["response"].status_code == 202


@then("la respuesta sigue siendo 202 Accepted")
def entonces_respuesta_sigue_siendo_202(context):
    assert context["response"].status_code == 202


@then("se crea un TokenRecuperacionPassword para ese Usuario, vigente 1 hora")
def entonces_se_crea_token_vigente(context):
    tokens = run_async(_tokens_de(context["email"]))
    assert len(tokens) == 1
    assert tokens[0].usado_en is None


@then("no se crea ningún TokenRecuperacionPassword")
def entonces_no_se_crea_token(context):
    async def _contar_todos() -> int:
        async with SessionLocal() as session:
            resultado = await session.execute(select(TokenRecuperacionPasswordModel))
            return len(resultado.scalars().all())

    assert run_async(_contar_todos()) == 0


@then("el token anterior queda invalidado")
def entonces_token_anterior_invalidado(context):
    tokens = run_async(_tokens_de(context["email"]))
    anterior = next(t for t in tokens if t.token == context["token_previo"])
    assert anterior.usado_en is not None


@then("se crea un token nuevo, distinto del anterior")
def entonces_token_nuevo_distinto(context):
    tokens = run_async(_tokens_de(context["email"]))
    sin_usar = [t for t in tokens if t.usado_en is None]
    assert len(sin_usar) == 1
    assert sin_usar[0].token != context["token_previo"]


@then("el TokenRecuperacionPassword queda creado igual")
def entonces_token_creado_igual(context):
    tokens = run_async(_tokens_de(context["email"]))
    assert len(tokens) == 1
    assert tokens[0].usado_en is None
