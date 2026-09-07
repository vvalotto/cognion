"""Steps BDD de US-ADJ-26 (`tests/features/inc4-adj/US-ADJ-26-generar-invitacion.feature`)."""

from __future__ import annotations

import asyncio
import threading
import uuid
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.settings import settings
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer

scenarios("../../features/inc4-adj/US-ADJ-26-generar-invitacion.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM invitacion"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision_docentes"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM usuario"))
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


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
    """Levanta un stub SMTP en un thread con loop propio — mismo patrón que
    `tests/step_defs/inc1/test_us_1_1_1_steps.py`, necesario para el escenario `@regression`
    que sí envía email (`email_destinatario` presente)."""
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


def _headers(usuario_id, perfil: TipoPerfil) -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(usuario_id, perfil)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


def _headers_administrador() -> dict[str, str]:
    return _headers(uuid4(), TipoPerfil.ADMINISTRADOR)


async def _crear_admin(session) -> Usuario:
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    return admin


async def _crear_docente(session) -> Usuario:
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    docente = Usuario.crear(
        "Docente", f"docente.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE
    )
    await usuario_repo.guardar(docente)
    return docente


async def _crear_docente_suelto() -> Usuario:
    """Crea un Docente sin asignarlo a ninguna comisión (sesión propia)."""
    async with SessionLocal() as session:
        return await _crear_docente(session)


async def _crear_comision_con_docente_asignado() -> tuple[Comision, Usuario]:
    async with SessionLocal() as session:
        admin = await _crear_admin(session)
        docente = await _crear_docente(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        comision.asignar_docente(docente.id)
        await comision_repo.actualizar(comision)
        return comision, docente


def _post(context, path: str, body: dict, headers) -> None:
    async def _call():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(path, json=body, headers=headers)

    context["response"] = run_async(_call())


@given("una comisión con un docente asignado")
def comision_con_docente(context):
    comision, docente = run_async(_crear_comision_con_docente_asignado())
    context["comision"] = comision
    context["docente"] = docente


@given("ese Docente ya generó una invitación para esa comisión")
def docente_ya_genero_invitacion(context):
    docente_headers = _headers(context["docente"].id, TipoPerfil.DOCENTE)
    _post(
        context,
        f"/comisiones/{context['comision'].id}/invitaciones",
        {"docente_id": str(context["docente"].id)},
        docente_headers,
    )
    assert context["response"].status_code == 201
    context["token_anterior"] = context["response"].json()["token"]


@given("una comisión sin el docente autenticado entre sus docentes_asignados")
def comision_sin_el_docente_autenticado(context):
    comision, docente_asignado = run_async(_crear_comision_con_docente_asignado())
    docente_ajeno = run_async(_crear_docente_suelto())
    context["comision"] = comision
    context["docente_asignado"] = docente_asignado
    context["docente"] = docente_ajeno


@given("un id de comisión que no existe")
def id_de_comision_inexistente(context):
    context["comision_id"] = uuid4()


@given("un Administrador autenticado")
def administrador_autenticado(context):
    comision, docente = run_async(_crear_comision_con_docente_asignado())
    context["comision"] = comision
    context["docente"] = docente


@when("ese Docente hace POST /comisiones/{comision_id}/invitaciones sin email_destinatario")
def docente_post_invitaciones_sin_email(context):
    docente_headers = _headers(context["docente"].id, TipoPerfil.DOCENTE)
    _post(
        context,
        f"/comisiones/{context['comision'].id}/invitaciones",
        {"docente_id": str(context["docente"].id)},
        docente_headers,
    )


@when("vuelve a hacer POST /comisiones/{comision_id}/invitaciones sin email_destinatario")
def docente_vuelve_a_post_invitaciones_sin_email(context):
    docente_post_invitaciones_sin_email(context)


@when("ese Docente hace POST /comisiones/{comision_id}/invitaciones con email_destinatario")
def docente_post_invitaciones_con_email(context):
    docente_headers = _headers(context["docente"].id, TipoPerfil.DOCENTE)
    _post(
        context,
        f"/comisiones/{context['comision'].id}/invitaciones",
        {
            "docente_id": str(context["docente"].id),
            "email_destinatario": "estudiante.adj26@fiuner.edu.ar",
        },
        docente_headers,
    )


@when("ese Docente hace POST /comisiones/{comision_id}/invitaciones")
def docente_no_asignado_post_invitaciones(context):
    docente_headers = _headers(context["docente"].id, TipoPerfil.DOCENTE)
    _post(
        context,
        f"/comisiones/{context['comision'].id}/invitaciones",
        {"docente_id": str(context["docente"].id)},
        docente_headers,
    )


@when("un Docente hace POST /comisiones/{id-inexistente}/invitaciones")
def docente_post_invitaciones_comision_inexistente(context):
    docente = run_async(_crear_docente_suelto())
    docente_headers = _headers(docente.id, TipoPerfil.DOCENTE)
    _post(
        context,
        f"/comisiones/{context['comision_id']}/invitaciones",
        {"docente_id": str(docente.id)},
        docente_headers,
    )


@when("hace POST /comisiones/{comision_id}/invitaciones")
def administrador_post_invitaciones(context):
    _post(
        context,
        f"/comisiones/{context['comision'].id}/invitaciones",
        {"docente_id": str(context["docente"].id)},
        _headers_administrador(),
    )


@then("recibe 201 con un token no vacío")
def valida_201_con_token(context):
    response = context["response"]
    assert response.status_code == 201
    assert response.json()["token"]


@then("recibe 201 con un token distinto del anterior")
def valida_201_token_distinto(context):
    response = context["response"]
    assert response.status_code == 201
    assert response.json()["token"] != context["token_anterior"]


@then("se envía el email de invitación")
def valida_email_enviado(context):
    assert context["response"].status_code == 201


@then("recibe 422")
def valida_422(context):
    assert context["response"].status_code == 422


@then("recibe 404")
def valida_404(context):
    assert context["response"].status_code == 404


@then("recibe 403")
def valida_403(context):
    assert context["response"].status_code == 403
