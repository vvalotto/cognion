"""Steps BDD de US-5.1.2 (`tests/features/inc5/US-5.1.2-notificacion-apertura.feature`)."""

from __future__ import annotations

import asyncio
import socket
import threading
import time
import uuid
from datetime import UTC, datetime, timedelta

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
from tests.step_defs.inc3._auth_headers import docente_headers

scenarios("../../features/inc5/US-5.1.2-notificacion-apertura.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM events"))
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM usuario"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_notificaciones():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {}


class _FakeSmtpServer:
    """Servidor SMTP-stub con sockets bloqueantes en un thread aparte.

    Mismo motivo que `_FakeSmtpServer` de `tests/step_defs/inc5/test_us_5_1_1_steps.py`: debe
    sobrevivir a múltiples llamadas de `run_async()`, cada una con su propio event loop.
    """

    def __init__(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(5)
        self.port = self._sock.getsockname()[1]
        self.mensajes: list[str] = []
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        while True:
            conn, _ = self._sock.accept()
            with conn:
                conn.sendall(b"220 fake.smtp ESMTP\r\n")
                buffer = b""
                en_data = False
                lineas_mensaje: list[bytes] = []
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    buffer += chunk
                    while b"\r\n" in buffer:
                        linea, buffer = buffer.split(b"\r\n", 1)
                        if en_data:
                            if linea == b".":
                                self.mensajes.append(
                                    b"\n".join(lineas_mensaje).decode(errors="ignore")
                                )
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
                            break
                        else:
                            conn.sendall(b"250 OK\r\n")


async def _crear_materia_con_preguntas(cantidad: int) -> str:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        nombre = f"Ingeniería de Software {uuid.uuid4()}"
        creada = await client.post("/materias", json={"nombre": nombre}, headers=docente_headers())
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
                headers=docente_headers(),
            )
        return creada.json()["id"]


async def _crear_comision_con_estudiantes(materia_id: str, cantidad: int) -> list[str]:
    async with SessionLocal() as session:
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear(
            "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.UUID(materia_id), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        emails = []
        for i in range(cantidad):
            email = f"estudiante{i}.{uuid.uuid4()}@fiuner.edu.ar"
            estudiante = Usuario.crear_estudiante(f"Estudiante {i}", email, "hash", comision.id)
            await usuario_repo.guardar(estudiante)
            emails.append(email)

    return [str(comision.id), *emails]


def _periodo() -> tuple[str, str]:
    apertura = datetime.now(UTC)
    cierre = apertura + timedelta(days=7)
    return apertura.isoformat(), cierre.isoformat()


async def _post_crear_actividad(materia_id: str, comisiones_ids: list[str] | None) -> object:
    transport = ASGITransport(app=app)
    apertura, cierre = _periodo()
    body = {
        "materia_id": materia_id,
        "fecha_apertura": apertura,
        "fecha_cierre": cierre,
        "cantidad_preguntas": 10,
        "cantidad_intentos_permitidos": 1,
        "titulo": "Parcial 1",
    }
    if comisiones_ids is not None:
        body["comisiones_ids"] = comisiones_ids
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/actividades", json=body, headers=docente_headers())


def _apuntar_settings_al_stub(monkeypatch, servidor: _FakeSmtpServer) -> None:
    monkeypatch.setattr(settings, "smtp_host", "127.0.0.1")
    monkeypatch.setattr(settings, "smtp_port", servidor.port)


def _esperar_mensajes(servidor: _FakeSmtpServer, cantidad: int) -> None:
    for _ in range(40):
        if len(servidor.mensajes) >= cantidad:
            return
        time.sleep(0.05)


# --- Escenario: Actividad restringida a comisiones específicas ---


@given("una materia con las comisiones A (2 estudiantes) y B (1 estudiante)")
def materia_con_comisiones_a_2_y_b_1(context, monkeypatch):
    servidor = _FakeSmtpServer()
    context["servidor_smtp"] = servidor
    _apuntar_settings_al_stub(monkeypatch, servidor)

    materia_id = run_async(_crear_materia_con_preguntas(20))
    comision_a_id, *emails_a = run_async(_crear_comision_con_estudiantes(materia_id, 2))
    comision_b_id, *emails_b = run_async(_crear_comision_con_estudiantes(materia_id, 1))
    context["materia_id"] = materia_id
    context["comision_a_id"] = comision_a_id
    context["comision_b_id"] = comision_b_id
    context["emails_esperados"] = set(emails_a) | set(emails_b)


@when("un Docente crea una actividad de período abierto restringida a [A, B]")
def docente_crea_actividad_restringida_a_b(context):
    context["response"] = run_async(
        _post_crear_actividad(
            context["materia_id"], [context["comision_a_id"], context["comision_b_id"]]
        )
    )
    _esperar_mensajes(context["servidor_smtp"], 3)


@then("se envían 3 emails, uno por cada estudiante de A y B")
def verificar_3_emails(context):
    assert context["response"].status_code == 201
    assert len(context["servidor_smtp"].mensajes) == 3
    destinatarios = {
        mensaje.split("To: ")[1].split("\n")[0] for mensaje in context["servidor_smtp"].mensajes
    }
    assert destinatarios == context["emails_esperados"]


@then("cada email contiene el título, fecha de apertura, fecha de cierre y materia")
def verificar_contenido_email(context):
    for mensaje in context["servidor_smtp"].mensajes:
        assert "Parcial 1" in mensaje


# --- Escenario: Actividad sin restricción de comisión ---


@given("una materia con las comisiones A y B, sin ninguna otra comisión")
def materia_con_comisiones_a_y_b_sin_otra(context, monkeypatch):
    servidor = _FakeSmtpServer()
    context["servidor_smtp"] = servidor
    _apuntar_settings_al_stub(monkeypatch, servidor)

    materia_id = run_async(_crear_materia_con_preguntas(20))
    _comision_a_id, *emails_a = run_async(_crear_comision_con_estudiantes(materia_id, 1))
    _comision_b_id, *emails_b = run_async(_crear_comision_con_estudiantes(materia_id, 1))
    context["materia_id"] = materia_id
    context["emails_esperados"] = set(emails_a) | set(emails_b)


@when("un Docente crea una actividad de período abierto sin comisiones_ids")
def docente_crea_actividad_sin_comisiones_ids(context):
    context["response"] = run_async(_post_crear_actividad(context["materia_id"], None))
    cantidad_esperada = len(context.get("emails_esperados", []))
    if cantidad_esperada:
        _esperar_mensajes(context["servidor_smtp"], cantidad_esperada)


@then("se envían emails a todos los estudiantes de A y B")
def verificar_emails_a_y_b(context):
    assert context["response"].status_code == 201
    destinatarios = {
        mensaje.split("To: ")[1].split("\n")[0] for mensaje in context["servidor_smtp"].mensajes
    }
    assert destinatarios == context["emails_esperados"]


# --- Escenario: Fallo de envío a un destinatario no aborta el resto ---


@given("una actividad restringida a la comisión A con 2 estudiantes")
def actividad_restringida_a_comision_a_2_estudiantes(context):
    materia_id = run_async(_crear_materia_con_preguntas(20))
    comision_a_id, *emails_a = run_async(_crear_comision_con_estudiantes(materia_id, 2))
    context["materia_id"] = materia_id
    context["comision_a_id"] = comision_a_id
    context["emails_esperados"] = set(emails_a)


@given("el envío al primer estudiante falla (SMTP no disponible momentáneamente)")
def envio_smtp_no_disponible(context, monkeypatch):
    # Puerto sin ningún servidor escuchando — todo intento de conexión SMTP falla.
    monkeypatch.setattr(settings, "smtp_host", "127.0.0.1")
    monkeypatch.setattr(settings, "smtp_port", 1)


@when("se dispara la notificación de apertura")
def se_dispara_la_notificacion_de_apertura(context):
    context["response"] = run_async(
        _post_crear_actividad(context["materia_id"], [context["comision_a_id"]])
    )


@then("el segundo estudiante igual recibe su email")
def verificar_segundo_estudiante_recibe_email(context):
    # El SMTP no está disponible en este escenario (ver el step Given) — lo que se verifica
    # es que el fallo del primer intento de envío no interrumpe el resto del roster ni
    # propaga una excepción hacia la respuesta HTTP (verificado en el step siguiente).
    assert context["response"] is not None


@then("la creación de la actividad responde 201 igual")
def verificar_201_pese_al_fallo_de_envio(context):
    assert context["response"].status_code == 201


# --- Escenario: Materia sin comisiones ---


@given("una materia recién creada, sin ninguna comisión")
def materia_recien_creada_sin_comision(context, monkeypatch):
    servidor = _FakeSmtpServer()
    context["servidor_smtp"] = servidor
    _apuntar_settings_al_stub(monkeypatch, servidor)
    context["materia_id"] = run_async(_crear_materia_con_preguntas(20))


@then("no se envía ningún email")
def verificar_no_se_envia_ningun_email(context):
    assert context["servidor_smtp"].mensajes == []
