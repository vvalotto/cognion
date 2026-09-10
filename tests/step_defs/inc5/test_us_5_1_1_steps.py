"""Steps BDD de US-5.1.1 (`tests/features/inc5/US-5.1.1-infraestructura-notificaciones.feature`)."""

from __future__ import annotations

import asyncio
import socket
import threading
import time
import uuid
from uuid import uuid4

import pytest
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.gateways.comision_query_repository import (
    SQLAlchemyComisionQueryRepository,
)
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.notificaciones.frameworks.adapters.comision_consulta_port_in_process import (
    ComisionConsultaPortInProcess,
)
from src.notificaciones.frameworks.adapters.smtp_canal_envio import SmtpCanalEnvio
from src.settings import settings
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal

scenarios("../../features/inc5/US-5.1.1-infraestructura-notificaciones.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM usuario"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {}


async def _crear_admin(session) -> Usuario:
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    return admin


async def _crear_comision(materia_id: uuid.UUID | None = None) -> Comision:
    async with SessionLocal() as session:
        admin = await _crear_admin(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        comision = Comision.crear(materia_id or uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        return comision


async def _deshabilitar_comision(comision: Comision) -> None:
    async with SessionLocal() as session:
        comision_repo = SQLAlchemyComisionRepository(session)
        comision.deshabilitar()
        await comision_repo.actualizar(comision)


async def _inscribir_estudiante(comision_id: uuid.UUID, nombre: str) -> Usuario:
    async with SessionLocal() as session:
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        estudiante = Usuario.crear_estudiante(
            nombre, f"{nombre.lower()}.{uuid.uuid4()}@fiuner.edu.ar", "hash", comision_id
        )
        await usuario_repo.guardar(estudiante)
        return estudiante


class _FakeSmtpServer:
    """Servidor SMTP-stub con sockets bloqueantes en un thread aparte.

    A diferencia del fixture `fake_smtp_server` de `tests/integration/`, este stub debe
    sobrevivir a múltiples llamadas de `run_async()` (cada una arranca y cierra su propio
    event loop) — un `asyncio.start_server` no sirve porque su loop muere al terminar cada
    step. Un thread con sockets estándar no depende de ningún event loop en particular.
    """

    def __init__(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(1)
        self.port = self._sock.getsockname()[1]
        self.mensajes: list[str] = []
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        conn, _ = self._sock.accept()
        with conn:
            conn.sendall(b"220 fake.smtp ESMTP\r\n")
            buffer = b""
            en_data = False
            lineas_mensaje: list[bytes] = []
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    return
                buffer += chunk
                while b"\r\n" in buffer:
                    linea, buffer = buffer.split(b"\r\n", 1)
                    if en_data:
                        if linea == b".":
                            self.mensajes.append(b"\n".join(lineas_mensaje).decode(errors="ignore"))
                            conn.sendall(b"250 OK queued\r\n")
                            en_data = False
                            lineas_mensaje = []
                        else:
                            lineas_mensaje.append(linea)
                        continue
                    cmd = linea.decode(errors="ignore").strip().upper()
                    if cmd.startswith("DATA"):
                        conn.sendall(b"354 End data with <CR><LF>.<CR><LF>\r\n")
                        en_data = True
                    elif cmd.startswith("QUIT"):
                        conn.sendall(b"221 Bye\r\n")
                        return
                    else:
                        conn.sendall(b"250 OK\r\n")


# --- Escenario: Roster combinado de varias comisiones sin duplicados ---


@given("un estudiante inscripto en las comisiones A y B")
def estudiante_en_comisiones_a_y_b(context):
    comision_a = run_async(_crear_comision())
    comision_b = run_async(_crear_comision())
    context["comision_a"] = comision_a
    context["comision_b"] = comision_b
    context["estudiante_en_ambas"] = run_async(_inscribir_estudiante(comision_a.id, "Ana"))


@given("otro estudiante inscripto solo en la comisión A")
def otro_estudiante_solo_en_a(context):
    context["estudiante_solo_a"] = run_async(
        _inscribir_estudiante(context["comision_a"].id, "Bruno")
    )


@when("se invoca ComisionConsultaPort.listar_destinatarios([A, B])")
def invocar_listar_destinatarios_a_b(context):
    async def _invocar():
        async with SessionLocal() as session:
            port = ComisionConsultaPortInProcess(session)
            return await port.listar_destinatarios(
                [context["comision_a"].id, context["comision_b"].id]
            )

    context["resultado"] = run_async(_invocar())


@then("el roster devuelto tiene 2 destinatarios, sin el primero repetido")
def verificar_roster_sin_duplicados(context):
    resultado = context["resultado"]
    assert len(resultado) == 2
    assert {d.estudiante_id for d in resultado} == {
        context["estudiante_en_ambas"].id,
        context["estudiante_solo_a"].id,
    }


# --- Escenario: Resolver todas las comisiones de una materia ---


@given("una materia con 3 comisiones activas y 1 inactiva")
def materia_con_comisiones_activas_e_inactiva(context):
    materia_id = uuid4()
    comisiones_activas = [run_async(_crear_comision(materia_id)) for _ in range(3)]
    comision_inactiva = run_async(_crear_comision(materia_id))
    run_async(_deshabilitar_comision(comision_inactiva))
    context["materia_id"] = materia_id
    context["comisiones_activas"] = comisiones_activas


@when("se invoca ComisionConsultaPort.listar_comisiones_por_materia(materia_id)")
def invocar_listar_comisiones_por_materia(context):
    async def _invocar():
        async with SessionLocal() as session:
            port = ComisionConsultaPortInProcess(session)
            return await port.listar_comisiones_por_materia(context["materia_id"])

    context["resultado"] = run_async(_invocar())


@then("el roster devuelto tiene las 3 comisiones activas")
def verificar_comisiones_activas(context):
    assert set(context["resultado"]) == {c.id for c in context["comisiones_activas"]}


# --- Escenario: Comisión sin estudiantes ---


@given("una comisión recién creada, sin inscripciones")
def comision_recien_creada_sin_inscripciones(context):
    context["comision"] = run_async(_crear_comision())


@when("se invoca ComisionConsultaPort.listar_destinatarios([comision_id])")
def invocar_listar_destinatarios_comision_vacia(context):
    async def _invocar():
        async with SessionLocal() as session:
            port = ComisionConsultaPortInProcess(session)
            return await port.listar_destinatarios([context["comision"].id])

    context["resultado"] = run_async(_invocar())


@then("el roster devuelto está vacío")
def verificar_roster_vacio(context):
    assert context["resultado"] == []


# --- Escenario: Query de Identidad expone email sin romper el consumidor existente ---


@given("una comisión con 2 estudiantes inscriptos")
def comision_con_2_estudiantes(context):
    comision = run_async(_crear_comision())
    context["comision"] = comision
    context["estudiantes"] = [
        run_async(_inscribir_estudiante(comision.id, "Carla")),
        run_async(_inscribir_estudiante(comision.id, "Diego")),
    ]


@when("se invoca ComisionQueryPort.listar_estudiantes_con_email(comision_id)")
def invocar_listar_estudiantes_con_email(context):
    async def _invocar():
        async with SessionLocal() as session:
            query = SQLAlchemyComisionQueryRepository(session)
            return await query.listar_estudiantes_con_email(context["comision"].id)

    context["resultado_con_email"] = run_async(_invocar())


@then("cada elemento incluye id, nombre y email")
def verificar_elementos_incluyen_email(context):
    resultado = context["resultado_con_email"]
    assert len(resultado) == 2
    for elemento in resultado:
        assert elemento.id is not None
        assert elemento.nombre
        assert elemento.email


@then("ComisionQueryPort.listar_estudiantes(comision_id) sigue devolviendo solo id y nombre")
def verificar_listar_estudiantes_sigue_igual(context):
    async def _invocar():
        async with SessionLocal() as session:
            query = SQLAlchemyComisionQueryRepository(session)
            return await query.listar_estudiantes(context["comision"].id)

    resultado = run_async(_invocar())
    assert len(resultado) == 2
    for elemento in resultado:
        assert not hasattr(elemento, "email")


# --- Escenario: Envío real contra el SMTP local de prueba ---


@given("el servidor SMTP de prueba corriendo localmente")
def servidor_smtp_de_prueba(context, monkeypatch):
    servidor = _FakeSmtpServer()
    context["servidor_smtp"] = servidor
    monkeypatch.setattr(settings, "smtp_host", "127.0.0.1")
    monkeypatch.setattr(settings, "smtp_port", servidor.port)


@when(
    'se invoca CanalEnvioPort.enviar("estudiante@example.com", "Asunto de prueba", '
    '"Cuerpo de prueba")'
)
def invocar_canal_envio_enviar(context):
    async def _invocar():
        canal = SmtpCanalEnvio()
        await canal.enviar("estudiante@example.com", "Asunto de prueba", "Cuerpo de prueba")

    run_async(_invocar())


@then("el mensaje aparece en la bandeja del servidor de prueba con ese asunto y destinatario")
def verificar_mensaje_en_bandeja(context):
    servidor = context["servidor_smtp"]
    for _ in range(20):
        if servidor.mensajes:
            break
        time.sleep(0.05)
    assert len(servidor.mensajes) == 1
    mensaje = servidor.mensajes[0]
    assert "Subject: Asunto de prueba" in mensaje
    assert "To: estudiante@example.com" in mensaje
